def validate_email(email):
    matches = re.search(r"^[a-zA-Z0-9]+@northumbria\.ac\.uk$", email, re.IGNORECASE)
    if matches: 
        print ("Valid university")
        return True
    else: 
        print ("Invalid!")
        return False

email = input ("Enter your email: ").strip()

validate_email(email)