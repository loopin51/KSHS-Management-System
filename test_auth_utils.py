import unittest
from auth_utils import is_valid_email

class TestIsValidEmail(unittest.TestCase):

    def test_valid_emails(self):
        self.assertTrue(is_valid_email("user@example.com"), "Standard valid email")
        self.assertTrue(is_valid_email("firstname.lastname@example.com"), "Email with dot in local part")
        self.assertTrue(is_valid_email("email@subdomain.example.com"), "Email with subdomain")
        self.assertTrue(is_valid_email("firstname+lastname@example.com"), "Email with plus sign")
        self.assertTrue(is_valid_email("email@example.co.jp"), "Email with country code TLD")
        self.assertTrue(is_valid_email("1234567890@example.com"), "Email with numbers in local part")
        self.assertTrue(is_valid_email("email@example-one.com"), "Email with hyphen in domain")
        self.assertTrue(is_valid_email("_______@example.com"), "Email with underscores in local part")
        self.assertTrue(is_valid_email("email@example.name"), "Email with long TLD")
        self.assertTrue(is_valid_email("email@example.museum"), "Email with .museum TLD")
        self.assertTrue(is_valid_email("email@example.travel"), "Email with .travel TLD")
        self.assertTrue(is_valid_email("user123@example.com"), "user123@example.com")
        self.assertTrue(is_valid_email("user.name+tag@example.com"), "user.name+tag@example.com")
        # Our regex allows email starting with a dot, though not common
        self.assertTrue(is_valid_email(".user@example.com"), "Email starting with dot (allowed by current regex)")


    def test_invalid_emails(self):
        self.assertFalse(is_valid_email("plainaddress"), "Missing @ and domain")
        self.assertFalse(is_valid_email("@example.com"), "Missing local part")
        self.assertFalse(is_valid_email("user@"), "Missing domain name")
        self.assertFalse(is_valid_email("user@example"), "Missing TLD")
        self.assertFalse(is_valid_email("user@example."), "Missing TLD (ends with dot)")
        self.assertFalse(is_valid_email("user@.com"), "Domain starts with dot")
        self.assertFalse(is_valid_email("user@example.c"), "TLD too short")
        self.assertFalse(is_valid_email("user@example..com"), "Double dot in domain")
        self.assertFalse(is_valid_email("user @example.com"), "Space in email")
        self.assertFalse(is_valid_email("user@example.com (Joe Smith)"), "Email with comments")
        self.assertFalse(is_valid_email("user@example_domain.com"), "Underscore in domain (not allowed by this regex)")
        self.assertFalse(is_valid_email(""), "Empty string")
        # Test None, though type hinting should prevent, defensive check
        # self.assertFalse(is_valid_email(None), "None value") # is_valid_email has `if not email: return False`

if __name__ == '__main__':
    unittest.main()
