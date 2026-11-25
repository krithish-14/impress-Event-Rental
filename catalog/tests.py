import threading

from django.contrib.auth.models import User
from django.db import IntegrityError, connection, transaction
from django.test import Client, RequestFactory, TestCase, TransactionTestCase
from django.urls import reverse

from catalog.admin import ReviewAdmin
from catalog.models import (
    Category,
    CustomerProfile,
    Inquiry,
    InquiryItem,
    Product,
    Review,
    ReviewReport,
    ReviewVote,
)
from catalog.review_service import ReviewError, create_review, rating_summary, report_review, review_page, set_vote


def make_catalog(name="Banquet Chair", slug="banquet-chair"):
    category = Category.objects.create(
        slug=f"tables-{slug}",
        name="Tables",
        nav_label="Tables",
        image_url="https://example.com/tables.jpg",
    )
    return Product.objects.create(
        category=category,
        name=name,
        slug=slug,
        image_url="https://example.com/chair.jpg",
        qty="10 Nos",
        description="A sturdy banquet chair.",
    )


def make_customer(phone, email, first_name="Ada"):
    user = User.objects.create_user(
        username=phone,
        email=email,
        password="pass12345",
        first_name=first_name,
    )
    CustomerProfile.objects.create(user=user, phone=phone)
    return user


def make_rental(user, product, status=Inquiry.STATUS_COMPLETED, quantity=1):
    inquiry = Inquiry.objects.create(
        name=user.first_name,
        email=user.email,
        phone=user.username,
        message="Need chairs",
        user=user,
        product=product,
        quantity=quantity,
        status=status,
    )
    return InquiryItem.objects.create(
        inquiry=inquiry,
        product=product,
        product_name=product.name,
        quantity=quantity,
    )


class ReviewFlowTests(TestCase):
    def setUp(self):
        self.product = make_catalog()
        self.user = make_customer("9999999999", "ada@example.com")
        self.item = make_rental(self.user, self.product)
        self.client = Client()

    def test_completed_rental_can_be_reviewed(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("review_submit", args=[self.product.slug]),
            {"inquiry_item": self.item.pk, "rating": "5", "title": "Solid chairs", "body": "They arrived on time and looked good."},
        )
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get()
        self.assertTrue(review.verified_rental)
        self.assertEqual(review.status, Review.STATUS_PUBLISHED)
        self.assertEqual(review.user, self.user)

    def test_guest_cannot_submit(self):
        response = self.client.post(
            reverse("review_submit", args=[self.product.slug]),
            {"inquiry_item": self.item.pk, "rating": "5", "title": "Solid chairs", "body": "They arrived on time and looked good."},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertEqual(Review.objects.count(), 0)

    def test_cannot_review_another_customers_item(self):
        other = make_customer("8888888888", "bea@example.com", "Bea")
        with self.assertRaises(ReviewError):
            create_review(other, self.product, self.item.pk, 4, "Not mine", "This rental belongs to someone else.")

    def test_accepted_rental_is_not_reviewable(self):
        self.item.inquiry.status = Inquiry.STATUS_ACCEPTED
        self.item.inquiry.save(update_fields=["status"])
        with self.assertRaises(ReviewError):
            create_review(self.user, self.product, self.item.pk, 4, "Too early", "The rental is still out.")

    def test_customer_can_post_more_than_one_review(self):
        create_review(self.user, self.product, self.item.pk, 5, "Solid chairs", "They arrived on time and looked good.")
        create_review(self.user, self.product, self.item.pk, 4, "Again", "A second review for the same product.")
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product).count(), 2)
        self.client.force_login(self.user)
        page = self.client.get(self.product.get_absolute_url())
        self.assertContains(page, "Write a review")
        self.assertContains(page, "Submit review")
        self.assertContains(page, "fa-pen", count=2)
        self.assertContains(page, "fa-trash", count=2)
        self.assertNotContains(page, "Withdraw review")

    def test_invalid_ratings_are_rejected(self):
        self.client.force_login(self.user)
        for rating in ("0", "6", "4.5", "nope"):
            response = self.client.post(
                reverse("review_submit", args=[self.product.slug]),
                {"inquiry_item": self.item.pk, "rating": rating, "title": "Solid chairs", "body": "They arrived on time and looked good."},
                follow=True,
            )
            self.assertContains(response, "Choose a star rating")
        self.assertEqual(Review.objects.count(), 0)

    def test_database_rejects_rating_outside_bounds(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    user=self.user,
                    inquiry_item=self.item,
                    product=self.product,
                    rating=0,
                    title="Bad",
                    body="This should not be stored.",
                    verified_rental=True,
                )

    def test_pending_reviews_are_excluded_from_public_summary(self):
        review = create_review(self.user, self.product, self.item.pk, 1, "Waiting", "This review is not public yet.")
        review.status = Review.STATUS_HIDDEN
        review.save(update_fields=["status"])
        summary = rating_summary(self.product)
        self.assertEqual(summary["total"], 0)
        self.assertIsNone(summary["average"])
        page = self.client.get(self.product.get_absolute_url())
        self.assertNotContains(page, "AggregateRating")
        self.assertContains(page, "No reviews yet")
        self.assertNotContains(page, "ada@example.com")

    def test_a_new_review_is_visible_to_every_visitor(self):
        create_review(self.user, self.product, self.item.pk, 5, "Great", "Everyone can read this review.")
        page = self.client.get(self.product.get_absolute_url())
        self.assertContains(page, "Everyone can read this review.")
        self.assertContains(page, "Ada")
        self.assertContains(page, "AggregateRating")

    def test_publishing_updates_the_average(self):
        review = create_review(self.user, self.product, self.item.pk, 4, "Good set", "The chairs were comfortable for the dinner.")
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        summary = rating_summary(self.product)
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["average"], 4.0)
        self.assertEqual(summary["counts"][4], 1)

    def test_edit_hide_and_withdraw_keep_the_summary_accurate(self):
        from catalog.review_service import update_review, withdraw_review

        review = create_review(self.user, self.product, self.item.pk, 5, "Excellent", "Everything was delivered and collected.")
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        update_review(self.user, review, 2, "Changed", "I updated the review after the event.")
        review.refresh_from_db()
        self.assertEqual(review.status, Review.STATUS_PUBLISHED)
        self.assertEqual(rating_summary(self.product)["average"], 2.0)
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        review.status = Review.STATUS_HIDDEN
        review.save(update_fields=["status"])
        self.assertEqual(rating_summary(self.product)["total"], 0)
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        withdraw_review(self.user, review)
        self.assertEqual(rating_summary(self.product)["total"], 0)

    def test_withdraw_from_the_product_page(self):
        review = create_review(self.user, self.product, self.item.pk, 5, "Excellent", "Everything was delivered and collected.")
        self.client.force_login(self.user)
        response = self.client.post(reverse("review_withdraw", args=[review.pk]))
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.status, Review.STATUS_HIDDEN)

    def test_helpful_vote_is_unique_and_can_change(self):
        review = create_review(self.user, self.product, self.item.pk, 5, "Excellent", "Everything was delivered and collected.")
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        voter = make_customer("8888888888", "bea@example.com", "Bea")
        set_vote(voter, review, True)
        set_vote(voter, review, False)
        vote = ReviewVote.objects.get(review=review, user=voter)
        self.assertFalse(vote.is_helpful)
        self.assertEqual(ReviewVote.objects.filter(review=review, user=voter).count(), 1)
        with self.assertRaises(ReviewError):
            set_vote(self.user, review, True)

    def test_customer_cannot_moderate_or_open_admin(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin:catalog_review_changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_admin_can_see_a_report(self):
        review = create_review(self.user, self.product, self.item.pk, 2, "Late pickup", "Pickup was later than promised.")
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        reporter = make_customer("8888888888", "bea@example.com", "Bea")
        report_review(reporter, review, ReviewReport.REASON_OTHER)
        staff = User.objects.create_superuser("admin", "admin@example.com", "admin12345")
        self.client.force_login(staff)
        response = self.client.get(reverse("admin:catalog_reviewreport_changelist"))
        self.assertContains(response, "Late pickup")
        listed = self.client.get(reverse("admin:catalog_review_changelist"))
        self.assertContains(listed, "Late pickup")

    def test_malicious_review_text_is_escaped(self):
        review = create_review(
            self.user,
            self.product,
            self.item.pk,
            3,
            "Review",
            "<script>alert(1)</script> This was a normal rental.",
        )
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        page = self.client.get(self.product.get_absolute_url())
        self.assertNotContains(page, "<script>alert(1)</script>")
        self.assertContains(page, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_public_page_hides_private_customer_data(self):
        review = create_review(self.user, self.product, self.item.pk, 5, "Excellent", "Everything was delivered and collected.")
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        page = self.client.get(self.product.get_absolute_url())
        self.assertContains(page, "Ada")
        self.assertNotContains(page, "ada@example.com")
        self.assertNotContains(page, "9999999999")

    def test_any_signed_in_customer_can_review(self):
        reviewer = make_customer("6666666666", "no-rental@example.com", "Noor")
        self.client.force_login(reviewer)
        page = self.client.get(self.product.get_absolute_url())
        self.assertContains(page, "Write a review")
        self.assertContains(page, "Your review")
        self.assertContains(page, "Upload image")
        self.assertNotContains(page, "Review title")
        self.assertContains(page, "fa-star")
        response = self.client.post(
            reverse("review_submit", args=[self.product.slug]),
            {"rating": "4", "title": "Easy to use", "body": "We used this at a wedding and it looked right."},
        )
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(user=reviewer)
        self.assertFalse(review.verified_rental)
        self.assertIsNone(review.inquiry_item_id)

    def test_sorting_and_pagination(self):
        first = create_review(self.user, self.product, self.item.pk, 1, "First look", "The first rental was only average.")
        second_user = make_customer("8888888881", "high@example.com", "High")
        second_item = make_rental(second_user, self.product)
        second = create_review(second_user, self.product, second_item.pk, 5, "Second look", "The second rental was excellent.")
        extra_users = []
        for index in range(4):
            phone = f"777777777{index}"
            person = make_customer(phone, f"p{index}@example.com", f"Pat{index}")
            extra_users.append(person)
            item = make_rental(person, self.product)
            create_review(person, self.product, item.pk, 3, f"Extra {index}", "Another completed rental review for paging.")
        Review.objects.update(status=Review.STATUS_PUBLISHED)
        ranked = review_page(self.product, "highest", 1)
        self.assertEqual(ranked.object_list[0].title, "Second look")
        page = self.client.get(self.product.get_absolute_url() + "?review_sort=newest")
        self.assertContains(page, "The second rental was excellent.")
        self.assertContains(page, "The first rental was only average.")
        self.assertContains(page, "Previous review")
        self.assertEqual(first.rating, 1)
        self.assertEqual(second.rating, 5)

    def test_json_ld_matches_published_reviews_only(self):
        review = create_review(self.user, self.product, self.item.pk, 5, "Excellent night", "Everything was delivered and collected.")
        review.status = Review.STATUS_PUBLISHED
        review.save(update_fields=["status"])
        page = self.client.get(self.product.get_absolute_url())
        self.assertContains(page, '"@type": "AggregateRating"')
        self.assertContains(page, '"ratingValue": 5.0')
        self.assertContains(page, '"reviewCount": 1')
        self.assertContains(page, "Everything was delivered and collected.")
        self.assertNotContains(page, "ada@example.com")

    def test_accept_still_moves_stock_and_complete_returns_it(self):
        pending = make_rental(self.user, self.product, status=Inquiry.STATUS_PENDING)
        pending.inquiry.items.exclude(pk=pending.pk).delete()
        self.product.qty = "10 Nos"
        self.product.rented_qty = 0
        self.product.save(update_fields=["qty", "rented_qty"])
        ok, _message = pending.inquiry.accept()
        self.assertTrue(ok)
        self.product.refresh_from_db()
        self.assertEqual(self.product.qty_number, 9)
        ok, _message = pending.inquiry.complete()
        self.assertTrue(ok)
        self.product.refresh_from_db()
        self.assertEqual(self.product.qty_number, 10)
        self.assertEqual(pending.inquiry.status, Inquiry.STATUS_COMPLETED)

    def test_staff_response_records_a_timestamp(self):
        review = create_review(self.user, self.product, self.item.pk, 5, "Excellent", "Everything was delivered and collected.")
        staff = User.objects.create_superuser("admin", "admin@example.com", "admin12345")
        request = RequestFactory().get("/")
        request.user = staff
        review.response_text = "Thank you for renting with us."

        class Changed:
            changed_data = ["response_text"]

        ReviewAdmin(Review, None).save_model(request, review, Changed(), True)
        review.refresh_from_db()
        self.assertIsNotNone(review.response_at)
        self.assertEqual(review.response_text, "Thank you for renting with us.")


class ConcurrentReviewTests(TransactionTestCase):
    def test_concurrent_duplicate_requests_create_one_review(self):
        product = make_catalog(slug="concurrent-chair")
        user = make_customer("9999999991", "ada2@example.com")
        item = make_rental(user, product)
        errors = []

        def attempt():
            try:
                create_review(user, product, item.pk, 5, "Once only", "Concurrent submission should not duplicate.")
            except ReviewError as exc:
                errors.append(str(exc))
            finally:
                connection.close()

        threads = [threading.Thread(target=attempt) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(Review.objects.filter(user=user, product=product).count(), 2)
        self.assertEqual(Review.objects.filter(inquiry_item=item).count(), 1)
        self.assertFalse(errors)
