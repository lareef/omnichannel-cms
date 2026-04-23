# install dependencies in the frontend folder
cd frontend
npm install

# start Tailwind in watch mode (writes to backend/static/css/output.css)
npm run watch:css

The output file is backend/static/css/output.css (matches TAILWIND_CLI_PATH in settings.py).

If you prefer npx without installing, run:


npx tailwindcss -i ./src/input.css -o ../backend/static/css/output.css --watch

Before a push - Recommended production build command
npx tailwindcss -i ./src/input.css -o ../backend/static/css/output.css --minify
