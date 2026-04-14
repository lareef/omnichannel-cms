# Run your local server and use a tool like ngrok to expose it to the internet. Twilio needs a public URL to send the webhook to.
ngrok http 8000
# Then, update the Webhook URL in your Twilio Sandbox settings to the ngrok URL (e.g., https://your-ngrok-subdomain.ngrok.io/api/whatsapp-webhook/).

Send a test message from your linked WhatsApp number to the Twilio Sandbox number.

Check your Django logs to see the incoming message and the ticket creation.

Here's how to set up ngrok to expose your local Django development server to the internet for testing webhooks.

Step 1: Sign Up for a Free ngrok Account
Go to the ngrok signup page and create a free account. After logging in, go to your dashboard and copy your authtoken – you'll need it in the next step.

Step 2: Install ngrok on Ubuntu/WSL
The easiest method for Ubuntu is using snap or the official apt repository.

Method A: Install via Snap (Simplest)

bash
sudo snap install ngrok
Method B: Install via Apt (Official Repository)

bash
# Add the ngrok repository and its GPG key
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update
sudo apt install ngrok
To verify the installation, run: ngrok version.

Step 3: Authenticate ngrok
Run the following command in your terminal, replacing YOUR_AUTHTOKEN with the token you copied from your dashboard.

# bash
ngrok config add-authtoken YOUR_AUTHTOKEN
Step 4: Configure Django to Allow ngrok URLs
When you run ngrok, it provides a URL like https://xxxx.ngrok.io. To allow Django to serve your app on this URL, you need to add it to the ALLOWED_HOSTS list in your settings.py.

# python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.ngrok.io']
Adding .ngrok.io ensures any random subdomain from ngrok is allowed.

Step 5: Start Your Local Django Server
In one terminal window, navigate to your Django project's root directory (where manage.py is located) and start the development server.

# bash
python manage.py runserver

Step 6: Start the ngrok Tunnel
Open a new, second terminal window (keep the Django server running in the first). Navigate to your project's root directory again and run the following command to create a tunnel on port 8000 (the default Django port).

# bash
ngrok http 8000

After the command runs, you'll see a status screen in your terminal. Look for the "Forwarding" line. It will show a public URL like https://xxxx.ngrok.io. This is your public endpoint. Requests sent to this address are securely tunneled to your local server at http://localhost:8000.

Step 7: Update the Twilio Webhook URL
Copy the HTTPS forwarding URL from the ngrok terminal (e.g., https://xxxx.ngrok.io). In your Twilio Console, go to Messaging > Try it Out > Send a WhatsApp message to access your Sandbox settings. Paste your ngrok URL into the webhook field, followed by the path of your Django view. The full URL should look like this:
https://xxxx.ngrok.io/api/whatsapp-webhook/

Don't forget to save your changes.

💡 Helpful Tips
Keep It Running: Both your Django server and the ngrok tunnel must stay running in their respective terminals for the webhook to be accessible.

Use the Inspector: ngrok's built-in Traffic Inspector (accessible at http://127.0.0.1:4040) is an invaluable tool for debugging. It lets you view every request that comes through the tunnel, including its headers and body.

For Production: ngrok is only for development and testing. For a production system, you should use a properly configured web server with a domain name.

Once you've confirmed that your webhook is working, you can test the full integration by sending a message from your WhatsApp to the Twilio sandbox number. The request will be tunneled directly to your local Django app.

