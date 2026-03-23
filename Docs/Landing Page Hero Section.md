🎨 Updated Landing Page Hero Section (with SVG)
Replace the hero section in your public/landing.html with this version. The SVG is fully responsive and adapts to the container.

html
{% extends 'base.html' %}
{% load static %}

{% block title %}OmniCMS – Enterprise Complaint Management{% endblock %}

{% block content %}
<!-- Hero Section -->
<section class="relative bg-white overflow-hidden">
    <div class="max-w-7xl mx-auto">
        <div class="relative z-10 pb-8 bg-white sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
            <main class="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
                <div class="sm:text-center lg:text-left">
                    <h1 class="text-4xl tracking-tight font-extrabold text-gray-900 sm:text-5xl md:text-6xl">
                        <span class="block xl:inline">Unified Omnichannel</span>
                        <span class="block text-indigo-600 xl:inline">Complaint Management</span>
                    </h1>
                    <p class="mt-3 text-base text-gray-500 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                        Centralize complaints from WhatsApp, Email, Web, and Phone. Enforce SLA accountability, empower agents with role‑based dashboards, and prepare for AI‑driven insights.
                    </p>
                    <div class="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                        <div class="rounded-md shadow">
                            <a href="{% url 'submit_complaint' %}" class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 md:py-4 md:text-lg md:px-10">
                                Submit a Complaint
                            </a>
                        </div>
                        <div class="mt-3 sm:mt-0 sm:ml-3">
                            {% if user.is_authenticated %}
                                <a href="{% url 'dashboard' %}" class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 md:py-4 md:text-lg md:px-10">
                                    Go to Dashboard
                                </a>
                            {% else %}
                                <a href="{% url 'account_login' %}" class="w-full flex items-center justify-center px-8 py-3 border border-transparent text-base font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 md:py-4 md:text-lg md:px-10">
                                    Agent Login
                                </a>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>
    <!-- Modern digital graphic (replaces the photo) -->
    <div class="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2 flex items-center justify-center p-8">
        <div class="w-full h-full max-h-[500px]">
            <svg viewBox="0 0 600 500" preserveAspectRatio="xMidYMid meet" class="w-full h-full">
                <!-- Background gradient -->
                <defs>
                    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#f0f5ff" stop-opacity="0.8" />
                        <stop offset="100%" stop-color="#e0e7ff" stop-opacity="0.5" />
                    </linearGradient>
                    <linearGradient id="circleGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#4f46e5" stop-opacity="0.2" />
                        <stop offset="100%" stop-color="#818cf8" stop-opacity="0.1" />
                    </linearGradient>
                    <linearGradient id="circleGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stop-color="#ec4899" stop-opacity="0.15" />
                        <stop offset="100%" stop-color="#f472b6" stop-opacity="0.05" />
                    </linearGradient>
                </defs>
                <rect width="600" height="500" fill="url(#bgGrad)" />

                <!-- Abstract communication lines (flow) -->
                <path d="M50 350 Q200 200, 350 350 T550 350" stroke="#4f46e5" stroke-width="2" fill="none" stroke-dasharray="6 6" opacity="0.3" />
                <path d="M80 380 Q220 250, 380 380 T550 400" stroke="#ec4899" stroke-width="2" fill="none" stroke-dasharray="4 8" opacity="0.3" />

                <!-- Floating circles (channels) -->
                <circle cx="120" cy="120" r="40" fill="url(#circleGrad1)" />
                <circle cx="450" cy="100" r="30" fill="url(#circleGrad2)" />
                <circle cx="500" cy="300" r="50" fill="url(#circleGrad1)" />
                <circle cx="150" cy="400" r="45" fill="url(#circleGrad2)" />

                <!-- Simple icon representations (chat, email, phone) -->
                <!-- Chat bubble -->
                <path d="M280 180 L300 160 L340 160 L360 180 L340 200 L300 200 Z" fill="#4f46e5" fill-opacity="0.6" />
                <circle cx="310" cy="176" r="4" fill="white" />
                <circle cx="330" cy="176" r="4" fill="white" />
                <circle cx="350" cy="176" r="4" fill="white" />

                <!-- Email envelope -->
                <rect x="180" y="260" width="50" height="35" rx="5" fill="#ec4899" fill-opacity="0.6" />
                <polyline points="180 265, 205 280, 230 265" stroke="white" stroke-width="2" fill="none" />

                <!-- Phone handset -->
                <path d="M400 420 L420 400 L430 410 L410 430 Z" fill="#4f46e5" fill-opacity="0.7" />
                <rect x="390" y="430" width="30" height="15" rx="3" fill="#4f46e5" fill-opacity="0.7" />

                <!-- Small connecting dots (data points) -->
                <circle cx="250" cy="320" r="5" fill="#4f46e5" fill-opacity="0.5" />
                <circle cx="350" cy="280" r="6" fill="#ec4899" fill-opacity="0.5" />
                <circle cx="420" cy="200" r="4" fill="#4f46e5" fill-opacity="0.5" />
            </svg>
        </div>
    </div>
</section>

<!-- The rest of your landing page (features, stats, CTA) remains unchanged -->
... (rest of your template) ...
{% endblock %}
✨ What This SVG Does
Modern abstract design – Uses soft gradients, translucent circles, and clean lines.

Represents omnichannel – Icons for chat, email, and phone are subtly integrated.

Data flow – Dashed lines suggest information moving between channels.

Responsive – The SVG scales with its container, preserving aspect ratio.

Consistent color palette – Matches your site's indigo/pink accents.

You can easily customise the colors, shapes, or even add subtle CSS animations (e.g., pulsing circles) later if desired.

🛠️ How to Customise Further
Replace the gradient colours in <linearGradient> definitions.

Add more icons or adjust positions by editing the cx, cy, and path coordinates.

To make it truly unique, consider exporting a similar SVG from a tool like Figma or Illustrator.