from flask import Flask, request, render_template_string, jsonify
import requests
import random
import threading

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; TSTB; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
]

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def check_wordpress(site_url):
    headers = {'User-Agent': get_random_user_agent()}
    try:
        response = requests.get(site_url, headers=headers, timeout=request_timeout)
        headers = response.headers
        if 'wp-' in response.text or 'wordpress' in headers.get('X-Powered-By', '').lower() or 'wp-content' in response.text:
            return True
        return False
    except requests.RequestException as e:
        return False

def fetch_author_url(site_url, user_id):
    author_url = f"{site_url}/?author={user_id}"
    headers = {'User-Agent': get_random_user_agent()}
    try:
        response = requests.get(author_url, headers=headers, timeout=request_timeout, allow_redirects=True)
        if response.status_code == 200 and "/author/" in response.url:
            username = response.url.split("/author/")[1].strip("/")
            found_users.append(username)
    except requests.RequestException as e:
        pass

def author_enumeration(site_url):
    threads = []
    for user_id in range(1, 11):
        t = threading.Thread(target=fetch_author_url, args=(site_url, user_id))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def fetch_rest_api(site_url, endpoint):
    api_url = f"{site_url}{endpoint}"
    headers = {'User-Agent': get_random_user_agent()}
    try:
        response = requests.get(api_url, headers=headers, timeout=request_timeout)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                found_users.append(user['slug'])
    except requests.RequestException as e:
        pass

def rest_api_enumeration(site_url):
    rest_endpoints = [
        "/wp-json/wp/v2/users",
        "/wp-json/wp/v2/users/",
        "/wp-json/wp/v2/usErs",
        "/wp-json/wp/v2/uSers",
        "/wp-json/wp/v2/UsErS",
        "/wp-json/wp/v2/UseRs",
    ]
    threads = []
    for endpoint in rest_endpoints:
        t = threading.Thread(target=fetch_rest_api, args=(site_url, endpoint))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def fetch_user_details(site_url, user_id):
    user_url = f"{site_url}/wp-json/wp/v2/users/{user_id}"
    headers = {'User-Agent': get_random_user_agent()}
    try:
        response = requests.get(user_url, headers=headers, timeout=request_timeout)
        if response.status_code == 200:
            user_data = response.json()
    except requests.RequestException as e:
        pass

def user_details_check(site_url):
    threads = []
    for user_id in range(1, 11):
        t = threading.Thread(target=fetch_user_details, args=(site_url, user_id))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def wordpress_com_api_check(site_url):
    domain = site_url.replace("https://", "").replace("http://", "").strip("/")
    headers = {'User-Agent': get_random_user_agent()}
    api_url = f"https://public-api.wordpress.com/rest/v1.1/sites/{domain}/posts"
    try:
        response = requests.get(api_url, headers=headers, timeout=request_timeout)
        if response.status_code == 200:
            pass
    except requests.RequestException as e:
        pass

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    global request_timeout
    global found_users
    result_message = ""
    status = "success"

    if request.method == 'POST':
        site_url = request.form.get('site_url').strip()
        request_timeout = int(request.form.get('timeout', 5))
        concurrent_threads = int(request.form.get('threads', 5))
        found_users = []

        if not check_wordpress(site_url):
            result_message = f"{site_url} does not appear to be a WordPress site."
            status = "error"
        else:
            author_enumeration(site_url)
            rest_api_enumeration(site_url)
            user_details_check(site_url)
            wordpress_com_api_check(site_url)

            found_users = set(found_users)
            if found_users:
                result_message = f"Found the following usernames: {', '.join(found_users)}"
            else:
                result_message = f"No vulnerable username enumeration found on {site_url}."

        return jsonify({"status": status, "message": result_message})

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ICU-WP</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
                .container {
                    background: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    max-width: 600px;
                    width: 100%;
                    box-sizing: border-box;
                }
                h1 {
                    margin-top: 0;
                    color: #333;
                    text-align: center;
                }
                form {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                label {
                    margin-bottom: 5px;
                    font-weight: bold;
                }
                input[type="text"], input[type="number"], input[type="submit"] {
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    width: 100%;
                    box-sizing: border-box;
                }
                input[type="submit"] {
                    background-color: #4CAF50;
                    color: #fff;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                }
                input[type="submit"]:hover {
                    background-color: #45a049;
                }
                .loader {
                    display: none;
                    margin: 20px 0;
                    text-align: center;
                }
                .loader.show {
                    display: block;
                }
                .loader::before {
                    content: '';
                    display: inline-block;
                    width: 50px;
                    height: 50px;
                    border: 5px solid #f3f3f3;
                    border-radius: 50%;
                    border-top: 5px solid #3498db;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .result {
                    display: none;
                    margin-top: 20px;
                }
                .result.show {
                    display: block;
                }
                .result h2 {
                    color: #333;
                }
                .footer {
                    text-align: center;
                    margin-top: 20px;
                    font-size: 14px;
                    color: #777;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>ICU-WP: I See You, WordPress :D</h1>
                <form id="scan-form" method="post">
                    <label for="site_url">Enter the WordPress website URL:</label>
                    <input type="text" id="site_url" name="site_url" required>

                    <label for="timeout">Request timeout (seconds):</label>
                    <input type="number" id="timeout" name="timeout" value="5">

                    <label for="threads">Number of concurrent threads (0-10):</label>
                    <input type="number" id="threads" name="threads" value="5" min="0" max="10">

                    <input type="submit" value="Start Scan">
                </form>

                <div class="loader" id="loader"></div>
                <div class="result" id="result"></div>

                <div class="footer">
                    <p>Created by: <a href="https://x.com/AnonKryptiQuz" target="_blank" rel="noopener noreferrer">AnonKryptiQuz</a></p>
                </div>

            </div>

            <script>
                document.getElementById('scan-form').addEventListener('submit', function(event) {
                    event.preventDefault();
                    document.getElementById('loader').classList.add('show');
                    document.getElementById('result').classList.remove('show');

                    const formData = new FormData(this);
                    fetch('/', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('loader').classList.remove('show');
                        document.getElementById('result').classList.add('show');
                        const resultDiv = document.getElementById('result');
                        if (data.status === 'error') {
                            resultDiv.innerHTML = `<h2>Error</h2><p>${data.message}</p>`;
                        } else {
                            resultDiv.innerHTML = `<h2>Scan Results</h2><p>${data.message}</p>`;
                        }
                    })
                    .catch(error => {
                        document.getElementById('loader').classList.remove('show');
                        document.getElementById('result').classList.add('show');
                        document.getElementById('result').innerHTML = `<h2>Error</h2><p>An error occurred: ${error}</p>`;
                    });
                });
            </script>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
