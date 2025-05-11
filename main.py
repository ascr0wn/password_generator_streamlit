import random
import string
import streamlit as st
import pyperclip
import re
import json
import base64
import hashlib
from datetime import datetime
from io import BytesIO

# App title and description
st.set_page_config(page_title="Advanced Password Generator", page_icon="🔒", layout="wide")

# Theme and styling
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    if st.session_state.theme == 'light':
        st.session_state.theme = 'dark'
    else:
        st.session_state.theme = 'light'

# Apply theme
if st.session_state.theme == 'dark':
    st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# Title with custom styling
st.markdown(f"""
<h1 style='text-align: center; color: {'white' if st.session_state.theme == 'dark' else '#1E6091'};'>
    🔒 Advanced Password Generator
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<p style='text-align: center; font-size: 1.2em;'>
    Generate secure, customizable passwords with advanced options
</p>
""", unsafe_allow_html=True)

# Define character sets
LOWERCASE = string.ascii_lowercase
UPPERCASE = string.ascii_uppercase
DIGITS = string.digits
SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~"
SIMILAR_CHARS = "il1Lo0O"
AMBIGUOUS_CHARS = "{}[]()/\\'\"`~,;:.<>"
VOWELS = "aeiou"
CONSONANTS = "".join([c for c in LOWERCASE if c not in VOWELS])

# Sidebar for settings
with st.sidebar:
    st.header("Settings")

    # Theme toggle
    if st.button("Toggle Dark/Light Mode"):
        toggle_theme()

    # Generation mode
    st.subheader("Generation Mode")
    generation_mode = st.radio(
        "Select Password Type",
        ["Random", "Pronounceable", "PIN", "Passphrase", "Custom Pattern"]
    )

    if generation_mode == "Random":
        # Password length
        password_length = st.slider("Password Length", min_value=8, max_value=64, value=16, step=1)

        # Character type options
        st.subheader("Character Types")
        use_lowercase = st.checkbox("Lowercase (a-z)", value=True)
        use_uppercase = st.checkbox("Uppercase (A-Z)", value=True)
        use_digits = st.checkbox("Digits (0-9)", value=True)
        use_special = st.checkbox("Special Characters (!@#$...)", value=True)

        # Advanced options
        st.subheader("Advanced Options")
        exclude_similar = st.checkbox("Exclude Similar Characters (i, l, 1, L, o, 0, O)", value=False)
        exclude_ambiguous = st.checkbox("Exclude Ambiguous Characters ({, }, [, ], etc.)", value=False)
        ensure_all_types = st.checkbox("Ensure All Selected Types Are Used", value=True)

    elif generation_mode == "Pronounceable":
        password_length = st.slider("Password Length", min_value=8, max_value=20, value=10, step=1)
        capitalize = st.checkbox("Capitalize First Letter", value=True)
        add_number = st.checkbox("Add Number at End", value=True)
        add_special = st.checkbox("Add Special Character", value=True)

    elif generation_mode == "PIN":
        pin_length = st.slider("PIN Length", min_value=4, max_value=12, value=6, step=1)
        avoid_repeats = st.checkbox("Avoid Repeating Digits", value=True)
        avoid_sequences = st.checkbox("Avoid Sequential Digits (1234, 9876)", value=True)

    elif generation_mode == "Passphrase":
        word_count = st.slider("Number of Words", min_value=3, max_value=8, value=4, step=1)
        separator = st.selectbox("Word Separator", ["-", "_", ".", " ", ",", ":", ";", "!"])
        capitalize_words = st.checkbox("Capitalize Words", value=False)
        add_number_to_passphrase = st.checkbox("Add Number", value=True)

    elif generation_mode == "Custom Pattern":
        st.write("Define your pattern using:")
        st.write("- a: lowercase letter")
        st.write("- A: uppercase letter")
        st.write("- 9: digit")
        st.write("- #: special character")
        st.write("- x: any character")
        custom_pattern = st.text_input("Pattern", value="aaaA-999#")

    # Number of passwords to generate
    num_passwords = st.slider("Number of Passwords to Generate", min_value=1, max_value=10, value=1)

    # Breach check option
    check_breached = st.checkbox("Check if Password Has Been Breached", value=False)

    if check_breached:
        st.info("Note: This is a simulated breach check for demonstration purposes only.")

# Function to calculate password strength
def calculate_strength(password):
    strength = 0
    feedback = []

    # Length check
    if len(password) >= 12:
        strength += 25
        feedback.append("Good length")
    elif len(password) >= 8:
        strength += 15
        feedback.append("Acceptable length")
    else:
        feedback.append("Password is too short")

    # Character variety checks
    if re.search(r'[a-z]', password):
        strength += 10
    else:
        feedback.append("Missing lowercase letters")

    if re.search(r'[A-Z]', password):
        strength += 10
    else:
        feedback.append("Missing uppercase letters")

    if re.search(r'[0-9]', password):
        strength += 10
    else:
        feedback.append("Missing numbers")

    if re.search(r'[^a-zA-Z0-9]', password):
        strength += 15
    else:
        feedback.append("Missing special characters")

    # Complexity checks
    if re.search(r'(.)\1\1', password):
        strength -= 10
        feedback.append("Contains repeating characters")

    if len(set(password)) < len(password) * 0.75:
        strength -= 5
        feedback.append("Low character variety")

    # Categorize strength
    if strength >= 60:
        category = "Strong"
        color = "green"
    elif strength >= 40:
        category = "Moderate"
        color = "orange"
    else:
        category = "Weak"
        color = "red"

    return strength, category, color, feedback

# Function to generate a random password
def generate_random_password(length, use_lower=True, use_upper=True, use_digits=True, use_special=True, 
                     exclude_similar=False, exclude_ambiguous=False, ensure_all_types=True):
    # Create character pool based on selected options
    char_pool = ""
    required_chars = []

    if use_lower:
        filtered_lower = LOWERCASE
        if exclude_similar:
            filtered_lower = ''.join([c for c in filtered_lower if c not in SIMILAR_CHARS])
        char_pool += filtered_lower
        if filtered_lower:  # Make sure we have at least one character
            required_chars.append(random.choice(filtered_lower))

    if use_upper:
        filtered_upper = UPPERCASE
        if exclude_similar:
            filtered_upper = ''.join([c for c in filtered_upper if c not in SIMILAR_CHARS])
        char_pool += filtered_upper
        if filtered_upper:  # Make sure we have at least one character
            required_chars.append(random.choice(filtered_upper))

    if use_digits:
        filtered_digits = DIGITS
        if exclude_similar:
            filtered_digits = ''.join([c for c in filtered_digits if c not in SIMILAR_CHARS])
        char_pool += filtered_digits
        if filtered_digits:  # Make sure we have at least one character
            required_chars.append(random.choice(filtered_digits))

    if use_special:
        filtered_special = SPECIAL_CHARS
        if exclude_ambiguous:
            filtered_special = ''.join([c for c in filtered_special if c not in AMBIGUOUS_CHARS])
        char_pool += filtered_special
        if filtered_special:  # Make sure we have at least one character
            required_chars.append(random.choice(filtered_special))

    # If exclude_ambiguous is selected, remove ambiguous characters from the pool
    if exclude_ambiguous:
        char_pool = ''.join([c for c in char_pool if c not in AMBIGUOUS_CHARS])

    # Ensure we have a valid character pool
    if not char_pool:
        st.error("Please select at least one character type")
        return None

    # Generate password
    if ensure_all_types and required_chars:
        # Make sure we have enough space for required characters
        if len(required_chars) > length:
            required_chars = required_chars[:length]

        # Generate the remaining characters
        remaining_length = length - len(required_chars)
        password_chars = [random.choice(char_pool) for _ in range(remaining_length)]

        # Add required characters
        password_chars.extend(required_chars)

        # Shuffle the password
        random.shuffle(password_chars)
        password = ''.join(password_chars)
    else:
        # Simple random selection
        password = ''.join(random.choice(char_pool) for _ in range(length))

    return password

# Function to generate a pronounceable password
def generate_pronounceable_password(length, capitalize=True, add_number=True, add_special=True):
    # Basic structure: consonant + vowel pairs
    password = ""

    # Generate consonant-vowel pairs until we reach desired length
    while len(password) < length - 4:  # Leave room for extras
        password += random.choice(CONSONANTS) + random.choice(VOWELS)

    # Trim to exact length if needed
    password = password[:length]

    # Apply options
    if capitalize:
        password = password.capitalize()

    # Add a number if requested and there's room
    if add_number and len(password) < length:
        password = password[:length-2] + str(random.randint(0, 99))

    # Add a special character if requested and there's room
    if add_special and len(password) < length:
        password = password[:length-1] + random.choice(SPECIAL_CHARS)

    return password

# Function to generate a PIN
def generate_pin(length, avoid_repeats=True, avoid_sequences=True):
    if avoid_repeats and avoid_sequences and length > 5:
        # For longer PINs with both constraints, we need a more complex approach
        digits = list(DIGITS)
        pin = []

        for i in range(length):
            # Filter out digits that would create repeats or sequences
            valid_digits = digits.copy()

            if avoid_repeats and pin:
                # Remove the last digit to avoid repeats
                if pin[-1] in valid_digits:
                    valid_digits.remove(pin[-1])

            if avoid_sequences and len(pin) >= 1:
                # Remove digits that would create ascending or descending sequences
                last_digit = int(pin[-1])
                if str(last_digit + 1) in valid_digits:
                    valid_digits.remove(str(last_digit + 1))
                if str(last_digit - 1) in valid_digits:
                    valid_digits.remove(str(last_digit - 1))

            # If we've filtered out all digits, relax constraints
            if not valid_digits:
                valid_digits = digits.copy()

            pin.append(random.choice(valid_digits))

        return ''.join(pin)
    else:
        # Simple approach for shorter PINs or fewer constraints
        while True:
            pin = ''.join(random.choice(DIGITS) for _ in range(length))

            # Check constraints
            if avoid_repeats and re.search(r'(.)\1', pin):
                continue

            if avoid_sequences:
                has_sequence = False
                for i in range(len(pin) - 1):
                    if abs(int(pin[i]) - int(pin[i+1])) == 1:
                        has_sequence = True
                        break
                if has_sequence:
                    continue

            return pin

# Common English words for passphrase generation
COMMON_WORDS = [
    "time", "year", "people", "way", "day", "man", "thing", "woman", "life", "child",
    "world", "school", "state", "family", "student", "group", "country", "problem", "hand", "part",
    "place", "case", "week", "company", "system", "program", "question", "work", "government", "number",
    "night", "point", "home", "water", "room", "mother", "area", "money", "story", "fact",
    "month", "lot", "right", "study", "book", "eye", "job", "word", "business", "issue",
    "side", "kind", "head", "house", "service", "friend", "father", "power", "hour", "game",
    "line", "end", "member", "law", "car", "city", "community", "name", "president", "team",
    "minute", "idea", "kid", "body", "information", "back", "parent", "face", "others", "level",
    "office", "door", "health", "person", "art", "war", "history", "party", "result", "change",
    "morning", "reason", "research", "girl", "guy", "moment", "air", "teacher", "force", "education"
]

# Function to generate a passphrase
def generate_passphrase(word_count, separator="-", capitalize_words=False, add_number=True):
    # Select random words
    words = random.sample(COMMON_WORDS, word_count)

    # Apply capitalization if requested
    if capitalize_words:
        words = [word.capitalize() for word in words]

    # Join with separator
    passphrase = separator.join(words)

    # Add a number if requested
    if add_number:
        passphrase += separator + str(random.randint(10, 99))

    return passphrase

# Function to generate a password based on a custom pattern
def generate_custom_password(pattern):
    password = ""

    for char in pattern:
        if char == 'a':
            password += random.choice(LOWERCASE)
        elif char == 'A':
            password += random.choice(UPPERCASE)
        elif char == '9':
            password += random.choice(DIGITS)
        elif char == '#':
            password += random.choice(SPECIAL_CHARS)
        elif char == 'x':
            # Any character
            all_chars = LOWERCASE + UPPERCASE + DIGITS + SPECIAL_CHARS
            password += random.choice(all_chars)
        else:
            # Keep literal characters
            password += char

    return password

# Function to check if a password has been breached (simulated)
def check_password_breach(password):
    # This is a simulated breach check
    # In a real application, you would use a service like the "Have I Been Pwned" API

    # For demonstration, we'll consider common passwords as "breached"
    common_passwords = [
        "password", "123456", "qwerty", "admin", "welcome", 
        "password123", "abc123", "letmein", "monkey", "1234567890"
    ]

    # Also consider passwords with simple patterns as "breached"
    if password.lower() in common_passwords:
        return True, "This password is commonly used and has likely been breached."

    # Check for simple patterns
    if re.match(r'^[a-z]+$', password) and len(password) < 8:
        return True, "Simple lowercase passwords are easily cracked."

    if re.match(r'^[0-9]+$', password):
        return True, "Numeric-only passwords are easily cracked."

    if re.match(r'^[a-z]+[0-9]{1,2}$', password):
        return True, "Simple word+number patterns are commonly breached."

    # Generate a hash of the password to simulate the HIBP API k-anonymity model
    password_hash = hashlib.sha1(password.encode()).hexdigest().upper()

    # Simulate a 5% chance of the password being breached for demonstration
    if random.random() < 0.05:
        return True, f"This password appears in a data breach. Hash prefix: {password_hash[:5]}..."

    return False, "No breaches found for this password."

# Function to create a downloadable file
def get_download_link(content, filename, text):
    b64 = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Initialize session state for password history if it doesn't exist
if 'password_history' not in st.session_state:
    st.session_state.password_history = []

# Generate button
if st.button("Generate Password(s)"):
    generated_passwords = []

    for _ in range(num_passwords):
        password = None

        # Generate password based on selected mode
        if generation_mode == "Random":
            password = generate_random_password(
                password_length, 
                use_lowercase, 
                use_uppercase, 
                use_digits, 
                use_special,
                exclude_similar,
                exclude_ambiguous,
                ensure_all_types
            )
        elif generation_mode == "Pronounceable":
            password = generate_pronounceable_password(
                password_length,
                capitalize,
                add_number,
                add_special
            )
        elif generation_mode == "PIN":
            password = generate_pin(
                pin_length,
                avoid_repeats,
                avoid_sequences
            )
        elif generation_mode == "Passphrase":
            password = generate_passphrase(
                word_count,
                separator,
                capitalize_words,
                add_number_to_passphrase
            )
        elif generation_mode == "Custom Pattern":
            password = generate_custom_password(custom_pattern)

        if password:
            # Check if password has been breached if option is selected
            breach_status = None
            if check_breached:
                is_breached, breach_message = check_password_breach(password)
                breach_status = {
                    'breached': is_breached,
                    'message': breach_message
                }

            # Add password to generated list
            generated_passwords.append({
                'password': password,
                'breach_status': breach_status
            })

            # Add to history with timestamp
            st.session_state.password_history.append({
                'password': password,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'length': len(password),
                'type': generation_mode
            })

    # Store in session state
    st.session_state.generated_passwords = generated_passwords

# Display generated passwords
if 'generated_passwords' in st.session_state and st.session_state.generated_passwords:
    st.subheader("Generated Passwords")

    # Add export all button
    if len(st.session_state.generated_passwords) > 0:
        export_content = "\n".join([p['password'] for p in st.session_state.generated_passwords])
        export_filename = f"passwords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        st.markdown(
            get_download_link(export_content, export_filename, "📥 Export All Passwords"),
            unsafe_allow_html=True
        )

    for i, password_data in enumerate(st.session_state.generated_passwords):
        password = password_data['password']
        breach_status = password_data.get('breach_status')

        # Use more columns if breach check is enabled
        if check_breached:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        else:
            col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.code(password)

        with col2:
            # Calculate and display password strength
            strength, category, color, feedback = calculate_strength(password)
            st.markdown(f"<span style='color:{color};font-weight:bold'>{category}</span>", unsafe_allow_html=True)

        with col3:
            if st.button(f"Copy #{i+1}", key=f"copy_{i}"):
                pyperclip.copy(password)
                st.success("Copied to clipboard!")

        # Show breach status if available
        if check_breached and breach_status:
            with col4:
                if breach_status['breached']:
                    st.markdown(f"<span style='color:red;font-weight:bold'>⚠️ Breached</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:green;font-weight:bold'>✅ Secure</span>", unsafe_allow_html=True)

        # Create expandable sections
        expander_cols = st.columns([1, 1])

        # Expandable section for password strength details
        with expander_cols[0]:
            with st.expander(f"Password #{i+1} Strength Details"):
                st.progress(min(strength/100, 1.0))
                st.write(f"Strength Score: {strength}/70")

                if feedback:
                    st.write("Feedback:")
                    for item in feedback:
                        st.write(f"- {item}")

        # Expandable section for breach details if available
        if check_breached and breach_status:
            with expander_cols[1]:
                with st.expander(f"Password #{i+1} Breach Details"):
                    st.write(breach_status['message'])
                    if breach_status['breached']:
                        st.warning("It's recommended to choose a different password.")
                    else:
                        st.success("This password hasn't been found in known data breaches.")

        st.markdown("---")

# Password history section
with st.expander("Password History"):
    if st.session_state.password_history:
        # Add export history button
        export_history_content = "\n".join([
            f"{p['password']} | {p.get('type', 'Random')} | {p['timestamp']}" 
            for p in st.session_state.password_history
        ])
        export_history_filename = f"password_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Clear History"):
                st.session_state.password_history = []
                st.experimental_rerun()

        with col2:
            st.markdown(
                get_download_link(export_history_content, export_history_filename, "📥 Export History"),
                unsafe_allow_html=True
            )

        # Display history table
        history_df = st.dataframe(
            st.session_state.password_history,
            column_config={
                "password": st.column_config.TextColumn("Password"),
                "timestamp": st.column_config.TextColumn("Generated At"),
                "length": st.column_config.NumberColumn("Length"),
                "type": st.column_config.TextColumn("Password Type")
            },
            hide_index=True
        )
    else:
        st.write("No passwords generated yet.")

# Tips section
with st.expander("Password Security Tips"):
    st.markdown("""
    ### Tips for Strong Passwords

    1. **Use long passwords** - Aim for at least 12 characters
    2. **Mix character types** - Include uppercase, lowercase, numbers, and special characters
    3. **Avoid personal information** - Don't use names, birthdays, or common words
    4. **Use different passwords** for different accounts
    5. **Consider a password manager** to store complex passwords securely

    ### What Makes a Password Weak?

    - Short length (less than 8 characters)
    - Using only one type of character (e.g., only lowercase)
    - Common words or patterns (password, 123456, qwerty)
    - Personal information that could be guessed
    - Reusing passwords across multiple sites
    """)

# Footer
st.markdown("---")
st.markdown("Created with ❤️ using Streamlit")
