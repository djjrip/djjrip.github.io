import unittest

from scripts.check_public_privacy import content_violations, path_violations


class TestPublicPrivacyGuard(unittest.TestCase):
    def test_public_business_email_is_allowed(self):
        self.assertEqual(content_violations("Contact: jquindao1@icloud.com"), [])

    def test_phone_number_is_blocked(self):
        self.assertIn("phone_number_or_tel_link", content_violations("Call (469) 555-0100"))

    def test_tel_link_is_blocked(self):
        self.assertIn("phone_number_or_tel_link", content_violations('<a href="tel:1234567890">Call</a>'))

    def test_ssn_pattern_is_blocked(self):
        self.assertIn("ssn_pattern", content_violations("SSN 123-45-6789"))

    def test_case_identifier_is_blocked(self):
        self.assertIn("case_or_edg_identifier", content_violations("Case #123456789"))

    def test_street_address_is_blocked(self):
        self.assertIn("street_address", content_violations("123 Main Street"))

    def test_private_snap_directory_is_blocked(self):
        self.assertIn("private_path", path_violations("snap/case.html"))

    def test_private_outreach_queue_is_blocked(self):
        self.assertIn("private_outreach_queue", path_violations("gaming-for-groceries/sponsor_outreach_queue.json"))

    def test_unreviewed_pdf_is_blocked(self):
        self.assertIn("unreviewed_pdf", path_violations("resume.pdf"))


if __name__ == "__main__":
    unittest.main()
