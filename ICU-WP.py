from flask import Flask, request, render_template_string, jsonify
import requests
import random
import concurrent.futures
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; AS; TSTB; rv:11.0) like Gecko",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
]

request_timeout = 5
found_users = []

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def make_request(url):
    headers = {'User-Agent': get_random_user_agent()}
    try:
        response = session.get(url, headers=headers, timeout=request_timeout)
        response.raise_for_status()
        return response
    except requests.RequestException:
        return None

def check_wordpress(site_url):
    response = make_request(site_url)
    if not response:
        return False
    
    if 'wp-' in response.text or 'wordpress' in response.headers.get('X-Powered-By', '').lower() or 'wp-content' in response.text:
        return True

    if '/wp-admin' in response.text or '/wp-login.php' in response.text:
        return True

    if 'WordPress' in response.headers.get('X-Powered-By', '') or 'WordPress' in response.headers.get('Server', ''):
        return True
    
    return False

def fetch_author_url(site_url, user_id):
    author_url = f"{site_url}/?author={user_id}"
    response = make_request(author_url)
    if response and response.status_code == 200 and "/author/" in response.url:
        username = response.url.split("/author/")[1].strip("/")
        found_users.append(username)

def author_enumeration(site_url, threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(fetch_author_url, site_url, user_id) for user_id in range(1, 11)]
        for future in concurrent.futures.as_completed(futures):
            future.result()

def fetch_rest_api(site_url, endpoint):
    api_url = f"{site_url}{endpoint}"
    response = make_request(api_url)
    if response and response.status_code == 200:
        users = response.json()
        for user in users:
            found_users.append(user['slug'])

def rest_api_enumeration(site_url, threads):
    rest_endpoints = [
        "/wp-json/wp/v2/users",
        "/wp-json/wp/v2/users/",
        "/wp-json/wp/v2/usErs",
        "/wp-json/wp/v2/uSers",
        "/wp-json/wp/v2/UsErS",
        "/wp-json/wp/v2/UseRs",
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(fetch_rest_api, site_url, endpoint) for endpoint in rest_endpoints]
        for future in concurrent.futures.as_completed(futures):
            future.result()

def fetch_user_details(site_url, user_id):
    user_url = f"{site_url}/wp-json/wp/v2/users/{user_id}"
    response = make_request(user_url)
    if response and response.status_code == 200:
        user_data = response.json()

def user_details_check(site_url, threads):
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(fetch_user_details, site_url, user_id) for user_id in range(1, 11)]
        for future in concurrent.futures.as_completed(futures):
            future.result()

def wordpress_com_api_check(site_url):
    domain = site_url.replace("https://", "").replace("http://", "").strip("/")
    api_url = f"https://public-api.wordpress.com/rest/v1.1/sites/{domain}/posts"
    response = make_request(api_url)
    if response and response.status_code == 200:
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
        threads = int(request.form.get('threads', 5))
        found_users = []

        if not check_wordpress(site_url):
            result_message = f"{site_url} does not appear to be a WordPress site."
            status = "error"
        else:
            author_enumeration(site_url, threads)
            rest_api_enumeration(site_url, threads)
            user_details_check(site_url, threads)
            wordpress_com_api_check(site_url)

            found_users = set(found_users)
            if found_users:
                result_message = f"Found the following usernames: {', '.join(found_users)}"
            else:
                result_message = f"No vulnerable username enumeration found on {site_url}."

        return jsonify({"status": status, "message": result_message})

    return render_template_string(r'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ICU-WP</title>
            <link rel="icon" href="https://upload.wikimedia.org/wikipedia/commons/a/a6/Anonymous_emblem.svg" type="image/svg+xml">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #181818;
                    color: #ddd;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    width: 100vw;
                    overflow: hidden;
                    position: relative;
                }

                .container-wrapper {
                    width: 110%;
                    height: 110%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    transform: scale(0.9); 
                    transform-origin: center center; 
                    overflow: hidden;
                }

                .container {
                    background: #212121;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 0 20px rgba(255, 255, 255, 0.3), 0 0 40px rgba(255, 255, 255, 0.5);
                    width: 100%;
                    max-width: 600px; 
                    box-sizing: border-box;
                    position: relative;
                    text-align: center;
                    z-index: 1;
                    transition: box-shadow 0.5s ease-in-out;
                }

                .logo {
                    width: 80px; 
                    height: 80px;
                    background-image: url('https://upload.wikimedia.org/wikipedia/commons/a/a6/Anonymous_emblem.svg');
                    background-size: cover;
                    margin-bottom: 20px;
                    position: absolute;
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                }

                h1 {
                    color: #00ff00;
                    font-size: 2em; 
                    text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00;
                    margin-top: 85px; 
                }

                form {
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }

                label {
                    margin-bottom: 5px;
                    font-weight: bold;
                    color: #ccc;
                }

                input[type="text"], input[type="number"], input[type="submit"] {
                    padding: 12px;
                    border: 1px solid #333;
                    border-radius: 4px;
                    width: 100%;
                    box-sizing: border-box;
                    background-color: #333;
                    color: #fff;
                }

                input[type="submit"] {
                    background-color: #00ff00;
                    color: #1c1c1c;
                    border: none;
                    cursor: pointer;
                    font-size: 16px;
                    transition: background-color 0.3s;
                }

                input[type="submit"]:hover {
                    background-color: #00cc00;
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
                    border-top: 5px solid #ffff00;
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
                    color: #00ff00;
                    text-shadow: 0 0 5px #00ff00;
                }

                .footer {
                    text-align: center;
                    margin-top: 30px;
                    font-size: 14px;
                    color: #aaa;
                }

                .footer a {
                    color: #00ff00;
                }

                .footer a:hover {
                    text-decoration: underline;
                }

                .bg-overlay {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 0; 
                }

                .anonymous-message {
                    font-size: 18px;
                    color: #ff0000;
                    text-shadow: 0 0 15px #ff0000;
                    font-weight: bold;
                    text-align: center;
                    margin-top: 30px;
                }

                @media (max-width: 600px) {
                    .container {
                        width: 100%;
                        padding: 15px;
                    }
                }
            </style>
        </head>
        <body>
            <div class="bg-overlay"></div>
            <div class="container-wrapper">
                <div class="container" id="container">
                    <div class="logo"></div>
                    <h1>ICU-WP: I See You, WordPress</h1>
                    <form id="scan-form" method="post">
                        <label for="site_url">Enter the WordPress website URL:</label>
                        <input type="text" id="site_url" name="site_url" required>

                        <label for="timeout">Request timeout (1-10 seconds):</label>
                        <input type="number" id="timeout" name="timeout" value="5" min="1" max="10">

                        <label for="threads">Number of concurrent threads (1-10):</label>
                        <input type="number" id="threads" name="threads" value="10" min="1" max="10">

                        <input type="submit" value="Start Scan">
                    </form>

                    <div class="loader" id="loader"></div>
                    <div class="result" id="result"></div>

                    <div class="footer">
                        <p>Created by: <a href="https://AnonKryptiQuz.github.io" target="_blank" rel="noopener noreferrer">AnonKryptiQuz</a></p>
                    </div>

                    <div class="anonymous-message">
                        <p>We are Anonymous. We are Legion. We do not forgive. We do not forget. Expect us.</p>
                    </div>
                </div>
            </div>

            <script>
                document.getElementById('scan-form').addEventListener('submit', function(event) {
                    event.preventDefault();
                    const siteUrl = document.getElementById('site_url').value.trim();

                    const urlPattern = /^(https?:\/\/)?([\w\d-]+(\.[\w\d-]+)+)(:\d+)?(\/[^\s]*)?$/i;
                    if (!urlPattern.test(siteUrl)) {
                        alert("Please enter a valid URL.");
                        return;
                    }

                    document.getElementById('loader').classList.add('show');
                    document.getElementById('result').classList.remove('show');
                    document.getElementById('container').style.boxShadow = '0 0 20px rgba(255, 255, 0, 0.3), 0 0 40px rgba(255, 255, 0, 0.5), 0 0 20px rgba(255, 255, 0, 0.3), 0 0 40px rgba(255, 255, 0, 0.5)';

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
                            document.getElementById('container').style.boxShadow = '0 0 20px rgba(255, 0, 0, 0.3), 0 0 40px rgba(255, 0, 0, 0.5), 0 0 20px rgba(255, 0, 0, 0.3), 0 0 40px rgba(255, 0, 0, 0.5)';
                            resultDiv.innerHTML = `<h2 style="color: #ff0000; text-shadow: 0 0 5px #ff0000;">Error</h2><p>${data.message}</p>`;
                        } else {
                            document.getElementById('container').style.boxShadow = '0 0 20px rgba(0, 255, 0, 0.3), 0 0 40px rgba(0, 255, 0, 0.5), 0 0 20px rgba(0, 255, 0, 0.3), 0 0 40px rgba(0, 255, 0, 0.5)';
                            resultDiv.innerHTML = `<h2>Scan Results</h2><p>${data.message}</p>`;
                        }
                    })

                    .catch(error => {
                        document.getElementById('loader').classList.remove('show');
                        document.getElementById('result').classList.add('show');
                        document.getElementById('container').style.boxShadow = '0 0 20px rgba(255, 0, 0, 0.3), 0 0 40px rgba(255, 0, 0, 0.5), 0 0 20px rgba(255, 0, 0, 0.3), 0 0 40px rgba(255, 0, 0, 0.5)';
                        document.getElementById('result').innerHTML = `<h2>Error</h2><p>${error.message}</p>`;
                    });
                });
            </script>
        </body>
        </html>
    ''')

if __name__ == '__main__':
    app.run(debug=True)
