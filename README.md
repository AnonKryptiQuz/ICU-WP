# ICU-WP: I See You, WordPress :D

**ICU-WP** is designed to scan WordPress sites for potential username enumeration vulnerabilities. This tool performs multiple checks to identify if a WordPress site is vulnerable to username enumeration through various methods.

## **Features**

- **WordPress Detection**: Identifies if a site is a WordPress installation.
- **Author Enumeration**: Attempts to enumerate usernames by querying author URLs.
- **REST API Enumeration**: Checks multiple REST API endpoints for user information.
- **User Details Check**: Attempts to fetch user details through REST API endpoints.
- **WordPress.com API Check**: Queries the WordPress.com public API for additional site information.

## **Prerequisites**

- **Python 3.7+**
- **Flask**
- **Requests**
- **Werkzeug**

## **Installation.**

1. **Clone the repository:**

   ```bash
   https://github.com/AnonKryptiQuz/ICU-WP.git
   cd ICU-WP
   ```

2. **Install the required packages:**

   ```bash
   pip install -r requirements.txt
   ```

   **Ensure `requirements.txt` contains:**

   ```text
   Flask
   requests
   Werkzeug
   ```

## **Usage**

1. **Run the Flask application:**

   ```bash
   python ICU-WP.py
   ```

2. **Open your browser and navigate to** `http://127.0.0.1:5000`.

3. **Enter the URL of the WordPress site you want to scan, set the request timeout and the number of concurrent threads, then click "Start Scan".**

## **Web Interface**

- **A simple HTML form is provided for users to enter the site URL and configuration settings.**
- **Results are displayed dynamically on the same page using JavaScript.**

## **Author**

**Created by:** [AnonKryptiQuz](https://AnonKryptiQuz.github.io/)
