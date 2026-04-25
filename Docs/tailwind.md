# install dependencies in the frontend folder
cd frontend
npm install

# start Tailwind in watch mode (writes to backend/static/css/output.css)
npm run watch:css

The output file is backend/static/css/output.css (matches TAILWIND_CLI_PATH in settings.py).

If you prefer npx without installing, run:


npx tailwindcss -i ./src/input.css -o ../backend/static/css/output.css --watch

Before a push - Recommended production build command - VPS
# output generated
npx tailwindcss -i ./src/input.css -o ../backend/static/css/output.css --minify
# Verify the new CSS file exists and is recent:
ls -la ~/omnichannel-cms/backend/static/css/output.css
# Copy the new CSS to the staticfiles directory (where Nginx serves from):
cp ~/omnichannel-cms/backend/static/css/output.css ~/omnichannel-cms/staticfiles/css/
# Run collectstatic to sync all static files (optional, but ensures consistency):
docker-compose -f ~/omnichannel-cms/docker-compose.prod.yml exec web python manage.py collectstatic --noinput
# Restart the web container
docker-compose -f ~/omnichannel-cms/docker-compose.prod.yml restart web


#  If it's still old, you may need to restart Nginx:
sudo systemctl reload nginx

## Instead of manually building on the VPS, commit the built output.css locally and push. Then your GitHub Actions will deploy it automatically. For now, the manual steps above will fix it.

