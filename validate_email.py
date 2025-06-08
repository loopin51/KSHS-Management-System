import re

email = "user@example.com"
# Corrected regex pattern to escape the dot in `\.`
pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

print(f"Testing email: {email}")
print(f"Using pattern: {pattern}")

if re.match(pattern, email):
    print(f"'{email}' is a valid email address according to the regex.")
else:
    print(f"'{email}' is an invalid email address according to the regex.")

# Test with a known invalid email to ensure the regex isn't too permissive
invalid_email = "notanemail"
print(f"Testing email: {invalid_email}")
if re.match(pattern, invalid_email):
    print(f"'{invalid_email}' is a valid email address according to the regex. This is unexpected.")
else:
    print(f"'{invalid_email}' is an invalid email address according to the regex. This is expected.")

# Test with an email that has a short domain extension (e.g., .c) which should be invalid
short_domain_email = "user@example.c"
print(f"Testing email: {short_domain_email}")
if re.match(pattern, short_domain_email):
    print(f"'{short_domain_email}' is a valid email address according to the regex. This is unexpected.")
else:
    print(f"'{short_domain_email}' is an invalid email address according to the regex. This is expected.")

# Test edge case: email with multiple subdomains
multi_subdomain_email = "user@sub.example.co.uk"
print(f"Testing email: {multi_subdomain_email}")
if re.match(pattern, multi_subdomain_email):
    print(f"'{multi_subdomain_email}' is a valid email address according to the regex. This is expected.")
else:
    print(f"'{multi_subdomain_email}' is an invalid email address according to the regex. This is unexpected.")
