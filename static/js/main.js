// AgroSmart AI - Frontend Control Panel

document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let currentLang = 'en'; // 'en' or 'kn'
    let currentTheme = 'dark';
    let predictionChartInstance = null;
    let predictionsHistoryData = [];

    // --- Selectors ---
    const body = document.body;
    const themeBtn = document.getElementById('theme-toggle');
    const langBtnEn = document.getElementById('lang-en');
    const langBtnKn = document.getElementById('lang-kn');
    const weatherCityInput = document.getElementById('weather-city-input');
    const weatherSearchBtn = document.getElementById('weather-search-btn');
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    // Form Selectors
    const predictorForm = document.getElementById('crop-predictor-form');
    const phInput = document.getElementById('input-ph');
    const phPointer = document.getElementById('ph-pointer');
    const predictorGrid = document.querySelector('.predictor-grid');
    const loadingOverlay = document.getElementById('loading-overlay');
    const resultCard = document.getElementById('result-card');
    const printReportBtn = document.getElementById('print-report-btn');
    
    // Result Selectors
    const resCropName = document.getElementById('res-crop-name');
    const resSoilBadge = document.getElementById('res-soil-badge');
    const resFertilizer = document.getElementById('res-fertilizer');
    const resIrrigation = document.getElementById('res-irrigation');
    const resSoilImprove = document.getElementById('res-soil-improve');
    const resIdealWeather = document.getElementById('res-ideal-weather');
    const resEstimatedIncome = document.getElementById('res-estimated-income');

    // Chatbot Selectors
    const chatBubble = document.getElementById('chat-bubble');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const quickReplies = document.querySelectorAll('.quick-reply-tag');

    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', () => {
            navMenu.classList.toggle('mobile-open');
            mobileMenuToggle.classList.toggle('active');
        });

        navMenu.querySelectorAll('.nav-link').forEach((navLink) => {
            navLink.addEventListener('click', () => {
                if (navMenu.classList.contains('mobile-open')) {
                    navMenu.classList.remove('mobile-open');
                    mobileMenuToggle.classList.remove('active');
                }
            });
        });

        window.addEventListener('resize', () => {
            if (window.innerWidth > 768 && navMenu.classList.contains('mobile-open')) {
                navMenu.classList.remove('mobile-open');
                mobileMenuToggle.classList.remove('active');
            }
        });
    }

    // Translation Dictionary
    const translations = {
        en: {
            logo_text: "AgroSmart AI",
            nav_home: "Home",
            nav_features: "Features",
            nav_predictor: "Predictor",
            nav_dashboard: "Dashboard",
            nav_about: "About",
            nav_profile: "Profile",
            nav_logout: "Logout",
            nav_admin: "Admin",
            nav_login: "Login",
            nav_register: "Register",
            hero_badge: "AI-Powered Smart Farming",
            hero_title: "AI-Based Smart <span>Crop Advisory</span> System",
            hero_subtitle: "Empowering farmers with state-of-the-art machine learning models to maximize yields, analyze soil health, and get real-time climate recommendations.",
            hero_get_started: "Get Recommendation",
            hero_learn_more: "Explore Dashboard",
            weather_title: "Farming Climate",
            weather_search_placeholder: "Enter city...",
            weather_humidity: "Humidity",
            weather_wind: "Wind",
            weather_rain: "Rain Prob.",
            feat_badge: "Key Capabilities",
            feat_title: "Intelligent Farm Management",
            feat_desc: "We bring modern data-driven agriculture tools straight to your field.",
            card_ml_title: "AI Crop Selection",
            card_ml_desc: "Get 95%+ accurate recommendations based on soil NPK levels, moisture, and rainfall parameters using Random Forest models.",
            card_soil_title: "pH Soil Analysis",
            card_soil_desc: "Understand your soil type (Acidic, Alkaline, or Neutral) and get targeted remediation strategies immediately.",
            card_eco_title: "Sustainable Practices",
            card_eco_desc: "Access eco-friendly fertilizer suggestions, water-saving irrigation guidelines, and green manure instructions.",
            card_chat_title: "24/7 Smart Advisor",
            card_chat_desc: "Chat with our virtual expert for answers on crop rotation, pest identification, weed management, and local practices.",
            form_title: "Input Soil Parameters",
            form_desc: "Fill in the parameters below. You can find these values from a standard soil health card.",
            lbl_nitrogen: "Nitrogen (N)",
            lbl_phosphorus: "Phosphorus (P)",
            lbl_potassium: "Potassium (K)",
            lbl_ph: "Soil pH",
            lbl_temp: "Temperature (°C)",
            lbl_humidity: "Humidity (%)",
            lbl_rainfall: "Rainfall (mm)",
            hint_nitrogen: "Optimal: 0 - 150 mg/kg",
            hint_phosphorus: "Optimal: 5 - 145 mg/kg",
            hint_potassium: "Optimal: 5 - 200 mg/kg",
            hint_ph: "Scale: 0.0 - 14.0",
            hint_temp: "Scale: 10 - 50 °C",
            hint_humidity: "Scale: 15 - 100 %",
            hint_rainfall: "Scale: 20 - 350 mm",
            btn_predict: "Predict Suitable Crop",
            btn_report: "Report",
            loading_predicting: "Analyzing Soil & Running ML Inference...",
            res_card_title: "AgroSmart Recommendation",
            res_card_subtitle: "Your AI Advisory Report is Ready",
            lbl_recommended: "RECOMMENDED CROP",
            lbl_fertilizer_tips: "Fertilizer Management",
            lbl_irrigation_tips: "Water & Irrigation",
            lbl_soil_tips: "Soil Enhancement",
            lbl_ideal_weather_tips: "Ideal Climate Conditions",
            lbl_income_tips: "Estimated Income & Value",
            report_label_ideal_weather: "Ideal Climate",
            report_label_estimated_income: "Market Value & Income Potential",
            profile_history_title: "Your Prediction History",
            no_history_msg: "No prediction history available yet. Run a prediction to store your history.",
            dash_badge: "Real-Time Tracking",
            dash_title: "Soil & Prediction Dashboard",
            stat_total: "Total Predictions",
            stat_avg_ph: "Average pH",
            stat_acidic: "Acidic Samples",
            stat_ideal: "Neutral Samples",
            chart_distribution: "Predicted Crop Distribution",
            chart_recent: "Prediction History Logs",
            about_badge: "How it works",
            about_title: "Bridging the Gap Between AI & Agriculture",
            about_desc_1: "AgroSmart AI utilizes machine learning algorithms (Random Forest Classifier) trained on extensive agronomic parameters to guide crop planning choices.",
            about_desc_2: "By examining critical physical and chemical metrics—such as Nitrogen, Phosphorus, Potassium, soil pH, and local weather indicators—our models output the highest probability matching crops, eliminating guesswork.",
            about_badge_organic: "100% Sustainable Suggestions",
            contact_badge: "Contact",
            footer_brand_desc: "AgroSmart AI is a futuristic smart agricultural platform dedicated to assisting farmers with localized insights and decision-making.",
            footer_links_title: "Quick Links",
            footer_rights: "All Rights Reserved.",
            chat_title: "Farmer Advisor AI",
            chat_placeholder: "Type a farming question...",
            qr_ph: "Soil pH",
            qr_fertilizer: "Fertilizers",
            qr_pest: "Pests Control",
            qr_water: "Drip Irrigation",
            validation_err: "Please enter valid numeric values within range for all inputs.",
            api_err: "Prediction failed. Using fallback system.",
            chat_welcome: "Hello! I am your AgroSmart AI Assistant. How can I help you with your crops, soil pH, or fertilizers today?",
            // Additional UI strings
            login_title: "Login to AgroSmart AI",
            login_username: "Username",
            login_password: "Password",
            login_btn: "Login",
            login_no_account: "Don't have an account?",
            signup_title: "Create a Farmer Profile",
            signup_username: "Username",
            signup_email: "Email",
            signup_password: "Password",
            signup_btn: "Register",
            signup_have_account: "Already registered?",
            profile_title: "Your Farmer Profile",
            profile_username_label: "Username:",
            profile_role_label: "Role:",
            profile_email_label: "Email:",
            export_csv: "Download CSV",
            export_xlsx: "Download Excel",
            report_title: "AgroSmart AI Prediction Report",
            report_generated_for: "Generated for",
            print_report: "Print Report",
            back_to_profile: "Back to Profile",
            report_section_summary: "Prediction Summary",
            report_section_parameters: "Soil Parameters",
            report_section_advice: "Agro Advice",
            admin_panel_title: "Admin Control Panel",
            admin_model_loaded: "Model loaded:",
            admin_reload_model: "Reload Model",
            admin_upload_model: "Upload Model or Dataset",
            admin_upload_hint: "Use the controls below to reload the model, upload new files, or add a training dataset.",
            admin_btn_upload: "Upload Files",
            admin_label_model_file: "Crop Model File (.pkl)",
            admin_label_classes_file: "Label Classes File (.pkl)",
            admin_label_dataset_file: "Training Dataset (CSV)",
            admin_section_training: "Training Pipeline",
            admin_training_desc: "To retrain or update the model, run the training script locally and upload the generated files here.",
            report_label_recommended: "Recommended Crop",
            report_label_soil_class: "Soil Classification",
            report_label_timestamp: "Timestamp",
            report_label_submitted_by: "Submitted By",
            report_label_temperature: "Temperature",
            report_label_humidity: "Humidity",
            report_label_ph: "pH",
            report_label_rainfall: "Rainfall",
            report_label_fertilizer: "Fertilizer",
            report_label_irrigation: "Irrigation",
            report_label_soil_care: "Soil Care",
        },
        kn: {
            logo_text: "ಅಗ್ರೋಸ್ಮಾರ್ಟ್ AI",
            nav_home: "ಮುಖಪುಟ",
            nav_features: "ವೈಶಿಷ್ಟ್ಯಗಳು",
            nav_predictor: "ಬೆಳೆ ಮುನ್ಸೂಚಕ",
            nav_dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
            nav_about: "ನಮ್ಮ ಬಗ್ಗೆ",
            nav_profile: "ಪ್ರೊಫೈಲ್",
            nav_logout: "ಲಾಗ್ಔಟ್",
            nav_admin: "ನಿರ್ವಾಹಕ",
            nav_login: "ಲಾಗಿನ್",
            nav_register: "ನೋಂದಣಿ",
            hero_badge: "AI ಆಧಾರಿತ ಸ್ಮಾರ್ಟ್ ಕೃಷಿ",
            hero_title: "AI-ಆಧಾರಿತ <span>ಸ್ಮಾರ್ಟ್ ಬೆಳೆ</span> ಸಲಹಾ ವ್ಯವಸ್ಥೆ",
            hero_subtitle: "ಇಳುವರಿಯನ್ನು ಗರಿಷ್ಠಗೊಳಿಸಲು, ಮಣ್ಣಿನ ಆರೋಗ್ಯವನ್ನು ವಿಶ್ಲೇಷಿಸಲು ಮತ್ತು ನೈಜ-ಸಮಯದ ಹವಾಮಾನ ಸಲಹೆಗಳನ್ನು ಪಡೆಯಲು ರೈತರಿಗೆ ಆಧುನಿಕ ಯಂತ್ರ ಕಲಿಕೆ ಮಾದರಿಗಳ ಮೂಲಕ ಸಹಾಯ ಮಾಡುವುದು.",
            hero_get_started: "ಬೆಳೆ ಶಿಫಾರಸು ಪಡೆಯಿರಿ",
            hero_learn_more: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್ ವೀಕ್ಷಿಸಿ",
            weather_title: "ಕೃಷಿ ಹವಾಮಾನ",
            weather_search_placeholder: "ನಗರದ ಹೆಸರು...",
            weather_humidity: "ಆರ್ದ್ರತೆ",
            weather_wind: "ಗಾಳಿ ವೇಗ",
            weather_rain: "ಮಳೆ ಸಾಧ್ಯತೆ",
            feat_badge: "ಮುಖ್ಯ ಸಾಮರ್ಥ್ಯಗಳು",
            feat_title: "ಬುದ್ಧಿವಂತ ಕೃಷಿ ನಿರ್ವಹಣೆ",
            feat_desc: "ನಾವು ಆಧುನಿಕ ಡೇಟಾ ಆಧಾರಿತ ಕೃಷಿ ಪರಿಕರಗಳನ್ನು ನೇರವಾಗಿ ನಿಮ್ಮ ಹೊಲಕ್ಕೆ ತರುತ್ತೇವೆ.",
            card_ml_title: "AI ಬೆಳೆ ಆಯ್ಕೆ",
            card_ml_desc: "ರಾಂಡಮ್ ಫಾರೆಸ್ಟ್ ಮಾದರಿಗಳನ್ನು ಬಳಸಿಕೊಂಡು ಮಣ್ಣಿನ NPK ಮಟ್ಟಗಳು ಮತ್ತು ಮಳೆಯ ಆಧಾರದ ಮೇಲೆ ಶೇ. 95 ಕ್ಕೂ ಹೆಚ್ಚು ನಿಖರವಾದ ಬೆಳೆ ಶಿಫಾರಸು ಪಡೆಯಿರಿ.",
            card_soil_title: "ಪಿಎಚ್ ಮಣ್ಣಿನ ವಿಶ್ಲೇಷಣೆ",
            card_soil_desc: "ನಿಮ್ಮ ಮಣ್ಣಿನ ಪ್ರಕಾರವನ್ನು (ಆಮ್ಲೀಯ, ಕ್ಷಾರೀಯ ಅಥವಾ ತಟಸ್ಥ) ಅರ್ಥಮಾಡಿಕೊಳ್ಳಿ ಮತ್ತು ತಕ್ಷಣ ಪರಿಹಾರ ಕ್ರಮಗಳನ್ನು ಕಂಡುಕೊಳ್ಳಿ.",
            card_eco_title: "ಸುಸ್ಥಿರ ಪದ್ಧತಿಗಳು",
            card_eco_desc: "ಪರಿಸರ ಸ್ನೇಹಿ ರಸಗೊಬ್ಬರ ಸಲಹೆಗಳು, ನೀರು ಉಳಿಸುವ ಹನಿ ನೀರಾವರಿ ಮಾರ್ಗಸೂಚಿಗಳು ಮತ್ತು ಹಸಿರೆಲೆ ಗೊಬ್ಬರದ ಮಾಹಿತಿ ಪಡೆಯಿರಿ.",
            card_chat_title: "24/7 ಸ್ಮಾರ್ಟ್ ಸಲಹೆಗಾರ",
            card_chat_desc: "ಬೆಳೆ ಸರದಿ, ಕೀಟ ನಿಯಂತ್ರಣ, ಕಳೆ ನಿರ್ವಹಣೆ ಮತ್ತು ಸ್ಥಳೀಯ ಕೃಷಿ ಪದ್ಧತಿಗಳ ಕುರಿತು ನಮ್ಮ ವರ್ಚುವಲ್ ತಜ್ಞರೊಂದಿಗೆ ಚಾಟ್ ಮಾಡಿ.",
            form_title: "ಮಣ್ಣಿನ ನಿಯತಾಂಕಗಳನ್ನು ನಮೂದಿಸಿ",
            form_desc: "ಕೆಳಗಿನ ಪಟ್ಟಿಯಲ್ಲಿ ಮಣ್ಣಿನ ಮೌಲ್ಯಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ. ನಿಮ್ಮ ಮಣ್ಣಿನ ಆರೋಗ್ಯ ಕಾರ್ಡ್‌ನಿಂದ ಈ ಮೌಲ್ಯಗಳನ್ನು ಪಡೆಯಬಹುದು.",
            lbl_nitrogen: "ಸಾರಜನಕ (N)",
            lbl_phosphorus: "ರಂಜಕ (P)",
            lbl_potassium: "ಪೊಟ್ಯಾಸಿಯಮ್ (K)",
            lbl_ph: "ಮಣ್ಣಿನ ಪಿಎಚ್",
            lbl_temp: "ತಾಪಮಾನ (°C)",
            lbl_humidity: "ಆರ್ದ್ರತೆ (%)",
            lbl_rainfall: "ಮಳೆ ಪ್ರಮಾಣ (mm)",
            hint_nitrogen: "ಸೂಕ್ತ: 0 - 150 mg/kg",
            hint_phosphorus: "ಸೂಕ್ತ: 5 - 145 mg/kg",
            hint_potassium: "ಸೂಕ್ತ: 5 - 200 mg/kg",
            hint_ph: "ವ್ಯಾಪ್ತಿ: 0.0 - 14.0",
            hint_temp: "ವ್ಯಾಪ್ತಿ: 10 - 50 °C",
            hint_humidity: "ವ್ಯಾಪ್ತಿ: 15 - 100 %",
            hint_rainfall: "ವ್ಯಾಪ್ತಿ: 20 - 350 mm",
            btn_predict: "ಸೂಕ್ತ ಬೆಳೆಯನ್ನು ಊಹಿಸಿ",
            btn_report: "ವರದಿ",
            loading_predicting: "ಮಣ್ಣು ವಿಶ್ಲೇಷಣೆ ಮತ್ತು AI ಲೆಕ್ಕಾಚಾರ ನಡೆಯುತ್ತಿದೆ...",
            res_card_title: "ಅಗ್ರೋಸ್ಮಾರ್ಟ್ ಶಿಫಾರಸು",
            res_card_subtitle: "ನಿಮ್ಮ AI ಕೃಷಿ ವರದಿ ಸಿದ್ಧವಾಗಿದೆ",
            lbl_recommended: "ಶಿಫಾರಸು ಮಾಡಿದ ಬೆಳೆ",
            lbl_fertilizer_tips: "ರಸಗೊಬ್ಬರ ನಿರ್ವಹಣೆ",
            lbl_irrigation_tips: "ನೀರು ಮತ್ತು ನೀರಾವರಿ",
            lbl_soil_tips: "ಮಣ್ಣಿನ ಫಲವತ್ತತೆ ಹೆಚ್ಚಳ",
            profile_history_title: "ನಿಮ್ಮ ಬೆಳೆ ಭವಿಷ್ಯವಾಣಿ ಇತಿಹಾಸ",
            no_history_msg: "ಇದುವರೆಗೆ ಯಾವ ಭವಿಷ್ಯವಾಣಿ ಇತಿಹಾಸವಿಲ್ಲ. ನಿಮ್ಮ ಇತಿಹಾಸವನ್ನು ಶೇಖರಿಸಲು ಒಂದು ಭವಿಷ್ಯವಾಣಿ ಚಲಾಯಿಸಿ.",
            dash_badge: "ನೈಜ-ಸಮಯದ ಟ್ರ್ಯಾಕಿಂಗ್",
            dash_title: "ಮಣ್ಣು ಮತ್ತು ಬೆಳೆ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
            stat_total: "ಒಟ್ಟು ಭವಿಷ್ಯವಾಣಿಗಳು",
            stat_avg_ph: "ಸರಾಸರಿ ಪಿಎಚ್",
            stat_acidic: "ಆಮ್ಲೀಯ ಮಾದರಿಗಳು",
            stat_ideal: "ತಟಸ್ಥ ಮಾದರಿಗಳು",
            chart_distribution: "ಶಿಫಾರಸು ಮಾಡಿದ ಬೆಳೆಗಳ ಹಂಚಿಕೆ",
            chart_recent: "ಇತ್ತೀಚಿನ ಮುನ್ಸೂಚನೆ ಲಾಗ್‌ಗಳು",
            about_badge: "ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
            about_title: "ಕೃಷಿ ಮತ್ತು ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆಯ ನಡುವೆ ಸೇತುವೆ",
            about_desc_1: "ಅಗ್ರೋಸ್ಮಾರ್ಟ್ AI ಮಣ್ಣಿನ ಭೌತಿಕ ಮತ್ತು ರಾಸಾಯನಿಕ ಲಕ್ಷಣಗಳ ಆಧಾರದ ಮೇಲೆ ಬೆಳೆ ಯೋಜನೆಗೆ ಮಾರ್ಗದರ್ಶನ ನೀಡಲು ಸುಧಾರಿತ ರಾಂಡಮ್ ಫಾರೆಸ್ಟ್ ಮಾದರಿಗಳನ್ನು ಬಳಸುತ್ತದೆ.",
            about_desc_2: "ಸಾರಜನಕ, ರಂಜಕ, ಪೊಟ್ಯಾಸಿಯಮ್, ಮಣ್ಣಿನ ಪಿಎಚ್ ಮತ್ತು ಸ್ಥಳೀಯ ಹವಾಮಾನ ಸೂಚಕಗಳಂತಹ ನಿರ್ಣಾಯಕ ಮಾಪನಗಳನ್ನು ಪರಿಶೀಲಿಸುವ ಮೂಲಕ, ಬೆಳೆ ಹೊಂದಾಣಿಕೆಗಳನ್ನು ನಮ್ಮ ಮಾದರಿಗಳು ಅತ್ಯಂತ ನಿಖರವಾಗಿ ಊಹಿಸುತ್ತವೆ.",
            about_badge_organic: "ಶೇ. 100 ಸುಸ್ಥಿರ ಕೃಷಿ ಸಲಹೆಗಳು",
            contact_badge: "ಸಂಪರ್ಕ",
            footer_brand_desc: "ಅಗ್ರೋಸ್ಮಾರ್ಟ್ AI ರೈತರಿಗೆ ಸ್ಥಳೀಯ ಒಳನೋಟಗಳು ಮತ್ತು ವೇಗದ ನಿರ್ಧಾರ ಕೈಗೊಳ್ಳಲು ನೆರವಾಗುವ ಅತ್ಯಾಧುನಿಕ ಸ್ಮಾರ್ಟ್ ಕೃಷಿ ವೇದಿಕೆಯಾಗಿದೆ.",
            footer_links_title: "ತ್ವರಿತ ಕೊಂಡಿಗಳು",
            footer_rights: "ಎಲ್ಲ ಹಕ್ಕುಗಳನ್ನು ಕಾಯ್ದಿರಿಸಲಾಗಿದೆ.",
            chat_title: "ರೈತ ಮಿತ್ರ AI",
            chat_placeholder: "ಕೃಷಿ ಪ್ರಶ್ನೆಗಳನ್ನು ಟೈಪ್ ಮಾಡಿ...",
            qr_ph: "ಮಣ್ಣಿನ ಪಿಎಚ್",
            qr_fertilizer: "ರಸಗೊಬ್ಬರಗಳು",
            qr_pest: "ಕೀಟ ನಿಯಂತ್ರಣ",
            qr_water: "ಹನಿ ನೀರಾವರಿ",
            validation_err: "ದಯವಿಟ್ಟು ಎಲ್ಲಾ ಇನ್‌ಪುಟ್‌ಗಳಿಗೆ ನಿಗದಿತ ವ್ಯಾಪ್ತಿಯಲ್ಲಿ ಸರಿಯಾದ ಸಂಖ್ಯಾತ್ಮಕ ಮೌಲ್ಯಗಳನ್ನು ನಮೂದಿಸಿ.",
            api_err: "ಊಹೆ ವಿಫಲವಾಗಿದೆ. ಪರ್ಯಾಯ ವ್ಯವಸ್ಥೆ ಬಳಸಲಾಗುತ್ತಿದೆ.",
            chat_welcome: "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಅಗ್ರೋಸ್ಮಾರ್ಟ್ ಕೃಷಿ ಸಲಹೆಗಾರ. ಇವತ್ತು ನಿಮಗೆ ಬೆಳೆಗಳು, ಮಣ್ಣಿನ ಪಿಎಚ್ ಅಥವಾ ರಸಗೊಬ್ಬರಗಳ ಬಗ್ಗೆ ಹೇಗೆ ಸಹಾಯಕ ಎಂದು?",
            // Additional Kannada UI strings
            login_title: "ಅಗ್ರೋಸ್ಮಾರ್ಟ್ AI ಗೆ ಲಾಗಿನ್",
            login_username: "ಬಳಕೆದಾರ ಹೆಸರು",
            login_password: "ಗುಪ್ತಪದ",
            login_btn: "ಲಾಗಿನ್",
            login_no_account: "ಖಾತೆ ಇಲ್ಲವೇ?",
            signup_title: "ರೈತ ಪ್ರೊಫೈಲ್ ರಚಿಸಿ",
            signup_username: "ಬಳಕೆದಾರ ಹೆಸರು",
            signup_email: "ಇಮೇಲ್",
            signup_password: "ಗುಪ್ತಪದ",
            signup_btn: "ನೋಂದಣಿ",
            signup_have_account: "ಇಲ್ಲಿಗೆ ನೋಂದಾಯಿತಾವೇ?",
            profile_title: "ನಿಮ್ಮ ರೈತ ಪ್ರೊಫೈಲ್",
            profile_username_label: "ಬಳಕೆದಾರ ಹೆಸರು:",
            profile_role_label: "ಹುದ್ದೆ:",
            profile_email_label: "ಇಮೇಲ್:",
            export_csv: "CSV ಡೌನ್‌ಲೋಡ್",
            export_xlsx: "Excel ಡೌನ್‌ಲೋಡ್",
            report_title: "ಅಗ್ರೋಸ್ಮಾರ್ಟ್ AI ಭವಿಷ್ಯವಾಣಿ ವರದಿ",
            report_generated_for: "ರಚಿಸಲಾಗಿದೆ:",
            print_report: "ವರದಿ ಮುದ್ರಣ",
            back_to_profile: "ಪ್ರೊಫೈಲ್‌ಗೆ ಹಿಂತಿರುಗಿ",
            report_section_summary: "ಭವಿಷ್ಯವಾಣಿ ಸಾರಾಂಶ",
            report_section_parameters: "ಮಣ್ಣು ನಿಯತಾಂಕಗಳು",
            report_section_advice: "ಕೃಷಿ ಸಲಹೆಗಳು",
            admin_panel_title: "ನಿರ್ವಾಹಕ ನಿಯಂತ್ರಣ ಫಲಕ",
            admin_model_loaded: "ಮಾದರಿ ಲೋಡ್ ಆಗಿದೆಯೇ:",
            admin_reload_model: "ಮಾದರಿಯನ್ನು ಮರು ಲೋಡ್ ಮಾಡಿ",
            admin_upload_model: "ಮಾದರಿ ಅಥವಾ ಡೇಟಾಸೆಟ್ ಅಪ್ಲೋಡ್ ಮಾಡಿ",
            admin_upload_hint: "ಮಾದರಿಯನ್ನು ಮರು ಲೋಡ್ ಮಾಡಲು, ಹೊಸ ಫೈಲ್‌ಗಳನ್ನು ಅಪ್ಲೋಡ್ ಮಾಡಲು ಅಥವಾ ತರಬೇತಿ ಡೇಟಾಸೆಟ್ ಸೇರಿಸಲು ಕೆಳಗಿನ ನಿಯಂತ್ರಣಗಳನ್ನು ಬಳಸಿ.",
            admin_btn_upload: "ಫೈಲ್ ಅಪ್ಲೋಡ್ ಮಾಡಿ",
            admin_label_model_file: "ಬೆಳೆ ಮಾದರಿ ಫೈಲ್ (.pkl)",
            admin_label_classes_file: "ಲೇಬಲ್ ವರ್ಗ ಫೈಲ್ (.pkl)",
            admin_label_dataset_file: "ತರಬೇತಿ ಡೇಟಾಸೆಟ್ (CSV)",
            admin_section_training: "ತರಬೇತಿ ಪೈಪ್‌ಲೈನ್",
            admin_training_desc: "ಮಾದರಿಯನ್ನು ಮರು ತರಬೇತು ಮಾಡಲು ಸ್ಥಳೀಯವಾಗಿ train_model.py ಚಲಾಯಿಸಿ ಮತ್ತು ಉತ್ಪತ್ತಿಯಾದ ಫೈಲ್‌ಗಳನ್ನು ಇಲ್ಲಿ ಅಪ್ಲೋಡ್ ಮಾಡಿ.",
            report_label_recommended: "ಶಿಫಾರಸು ಮಾಡಿದ ಬೆಳೆ",
            report_label_soil_class: "ಮಣ್ಣು ವರ್ಗೀಕರಣ",
            report_label_timestamp: "ಸಮಯ ಮುದ್ರೆ",
            report_label_submitted_by: "ಸಲ್ಲಿಸಿದವರು",
            report_label_temperature: "ತಾಪමාನ್",
            report_label_humidity: "ಆರ್ದ್ರತೆ",
            report_label_ph: "pH",
            report_label_rainfall: "ಮಳೆ ಪ್ರಮಾಣ",
            report_label_fertilizer: "ರಸಗೊಬ್ಬರ",
            report_label_irrigation: "ನೀರಾವರಿ",
            report_label_soil_care: "ಮಣ್ಣಿನ ಕಾಳಜಿ",
            lbl_ideal_weather_tips: "ಸೂಕ್ತ ಹವಾಮಾನ ಪರಿಸ್ಥಿತಿಗಳು",
            lbl_income_tips: "ಅಂದಾಜು ಆದಾಯ ಮತ್ತು ಮೌಲ್ಯ",
            report_label_ideal_weather: "ಸೂಕ್ತ ಹವಾಮಾನ",
            report_label_estimated_income: "ಮಾರುಕಟ್ಟೆ ಮೌಲ್ಯ ಮತ್ತು ಆದಾಯ ಸಾಮರ್ಥ್ಯ"
        }
    };

    // Crop translation names dictionary (English to Kannada)
    const cropTranslations = {
        'Rice': 'ಭತ್ತ (Rice)',
        'Maize': 'ಮೆಕ್ಕೆಜೋಳ (Maize)',
        'Chickpea': 'ಕಡಲೆ (Chickpea)',
        'Cotton': 'ಹತ್ತಿ (Cotton)',
        'Coconut': 'ತೆಂಗು (Coconut)',
        'Coffee': 'ಕಾಫಿ (Coffee)',
        'Banana': 'ಬಾಳೆಹಣ್ಣು (Banana)',
        'Mango': 'ಮಾವು (Mango)',
        'Grapes': 'ದ್ರಾಕ್ಷಿ (Grapes)',
        'Watermelon': 'ಕಲ್ಲಂಗಡಿ (Watermelon)',
        'Orange': 'ಕಿತ್ತಳೆ (Orange)',
        'Papaya': 'ಪಪ್ಪಾಯಿ (Papaya)'
    };

    // --- Core Functions ---

    // Toggle Theme (Futuristic Dark / Light)
    function toggleTheme() {
        if (currentTheme === 'dark') {
            body.setAttribute('data-theme', 'light');
            currentTheme = 'light';
            if (themeBtn) themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
            localStorage.setItem('theme', 'light');
        } else {
            body.removeAttribute('data-theme');
            currentTheme = 'dark';
            if (themeBtn) themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
            localStorage.setItem('theme', 'dark');
        }
    }

    // Set Theme on Load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        body.setAttribute('data-theme', 'light');
        currentTheme = 'light';
        if (themeBtn) themeBtn.innerHTML = '<i class="fas fa-moon"></i>';
    } else if (themeBtn) {
        themeBtn.innerHTML = '<i class="fas fa-sun"></i>';
    }

    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            toggleTheme();
            if (predictionsHistoryData.length) renderChart(predictionsHistoryData);
        });
    }

    // Apply Localization
    function applyLocalization(lang) {
        currentLang = lang;
        localStorage.setItem('lang', lang);

        if (lang === 'en') {
            if (langBtnEn) langBtnEn.classList.add('active');
            if (langBtnKn) langBtnKn.classList.remove('active');
        } else {
            if (langBtnEn) langBtnEn.classList.remove('active');
            if (langBtnKn) langBtnKn.classList.add('active');
        }

        // Translate all data-i18n elements
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (translations[lang][key]) {
                el.innerHTML = translations[lang][key];
            }
        });

        // Translate placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (translations[lang][key]) {
                el.setAttribute('placeholder', translations[lang][key]);
            }
        });

        // Translate crop names in profile/history/report lists
        document.querySelectorAll('.crop-name-translate').forEach(el => {
            const cropEn = el.getAttribute('data-crop');
            if (cropEn) {
                const localizedCrop = lang === 'en' ? cropEn : (cropTranslations[cropEn] || cropEn);
                el.textContent = localizedCrop;
            }
        });

        // Translate soil type in lists/reports
        document.querySelectorAll('.soil-type-translate').forEach(el => {
            const val = el.getAttribute(`data-${lang}`);
            if (val) el.textContent = val;
        });

        // Translate specific advisory advice cards in reports
        document.querySelectorAll('.advice-translate').forEach(el => {
            const val = el.getAttribute(`data-${lang}`);
            if (val) el.textContent = val;
        });

        // If prediction exists, update it based on current language
        if (lastPredictionResult && resCropName) {
            renderPredictionResult(lastPredictionResult);
        }
        
        // Refresh dashboard list showing localized crop names if container exists
        if (document.getElementById('history-list-container')) {
            renderHistoryList();
        }
    }

    if (langBtnEn) langBtnEn.addEventListener('click', () => applyLocalization('en'));
    if (langBtnKn) langBtnKn.addEventListener('click', () => applyLocalization('kn'));

    // Dynamic Header Scroll Effect
    window.addEventListener('scroll', () => {
        const header = document.querySelector('header');
        if (!header) return;
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });

    // --- Weather Widget Controller ---
    async function fetchWeather(city = 'bangalore') {
        try {
            const res = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
            const data = await res.json();
            if (data.success) {
                const cityEl = document.getElementById('weather-city-name');
                const tempEl = document.getElementById('weather-temp');
                const descEl = document.getElementById('weather-desc');
                const windEl = document.getElementById('weather-wind-val');
                const humEl = document.getElementById('weather-hum-val');
                const rainEl = document.getElementById('weather-rain-val');
                if (!cityEl || !tempEl) return;

                cityEl.textContent = data.city_name[currentLang];
                tempEl.textContent = `${data.temp}°C`;
                if (descEl) descEl.textContent = data.description[currentLang];
                if (windEl) windEl.textContent = `${data.wind_speed} km/h`;
                if (humEl) humEl.textContent = `${data.humidity}%`;
                if (rainEl) rainEl.textContent = `${data.rainfall_prob}%`;
                
                const iconEl = document.getElementById('weather-main-icon');
                if (!iconEl) return;
                iconEl.className = 'weather-icon-cloud fas ';
                if (data.rainfall_prob > 50) {
                    iconEl.classList.add('fa-cloud-showers-heavy');
                } else if (data.rainfall_prob > 15) {
                    iconEl.classList.add('fa-cloud-sun-rain');
                } else if (data.humidity > 70) {
                    iconEl.classList.add('fa-cloud');
                } else {
                    iconEl.classList.add('fa-sun');
                }
            }
        } catch (e) {
            console.error("Error fetching weather details:", e);
        }
    }

    if (weatherSearchBtn) {
        weatherSearchBtn.addEventListener('click', () => {
            const city = weatherCityInput ? weatherCityInput.value.trim() : '';
            if (city) {
                fetchWeather(city);
            }
        });
    }

    if (weatherCityInput) {
        weatherCityInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const city = weatherCityInput.value.trim();
                if (city) {
                    fetchWeather(city);
                }
            }
        });
    }

    // Initial weather fetch (only on pages with widget)
    if (typeof fetchWeather === 'function' && (weatherCityInput || document.getElementById('weather-city-name'))) {
        fetchWeather('bangalore');
    }

    // --- pH Interactive Pointer Slider ---
    if (phInput) {
        phInput.addEventListener('input', () => {
            const phVal = parseFloat(phInput.value);
            if (!isNaN(phVal) && phVal >= 0 && phVal <= 14 && phPointer) {
                const percentage = (phVal / 14) * 100;
                phPointer.style.left = `${percentage}%`;
            }
        });
    }

    // --- Crop Predictor Pipeline ---
    let lastPredictionResult = null;

    function hidePredictionResult() {
        if (!resultCard) return;
        resultCard.classList.remove('show', 'result-pop', 'reveal-on-scroll', 'revealed');
        resultCard.setAttribute('aria-hidden', 'true');
        resultCard.setAttribute('hidden', '');
        if (predictorGrid) predictorGrid.classList.remove('active-result');
    }

    function showPredictionResult() {
        if (!resultCard) return;
        resultCard.classList.remove('reveal-on-scroll', 'revealed');
        resultCard.setAttribute('aria-hidden', 'false');
    }

    hidePredictionResult();

    function renderPredictionResult(data) {
        if (!data || !resCropName) return;
        
        // Show crop translation if Kannada is selected
        const cropEn = data.crop || data.recommended_crop || '';
        const cropNameToShow = currentLang === 'en' ? cropEn : (cropTranslations[cropEn] || cropEn);
        resCropName.textContent = cropNameToShow;
        
        // Soil Class badge
        const soilClass = data.soil_classification || data.soil_type_localized || {};
        const soilText = soilClass[currentLang] || soilClass.en || data.soil_type || '';
        if (resSoilBadge) {
            resSoilBadge.textContent = soilText;
            resSoilBadge.className = 'result-soil-badge ';
        }
        
        // Color-code the badge based on pH class
        const soilEn = (soilClass.en || data.soil_type || '').toLowerCase();
        if (resSoilBadge) {
            if (soilEn.includes('acidic')) {
                resSoilBadge.classList.add('acidic');
            } else if (soilEn.includes('alkaline')) {
                resSoilBadge.classList.add('alkaline');
            } else {
                resSoilBadge.classList.add('neutral');
            }
        }

        // Suggestions
        const advice = data.advice || {};
        const fertilizerAdvice = advice.fertilizer || {};
        const irrigationAdvice = advice.irrigation || {};
        const soilAdvice = advice.soil_improvement || advice.soil || {};

        const weatherAdvice = advice.ideal_weather || {};
        const incomeAdvice = advice.estimated_income || {};

        if (resFertilizer) resFertilizer.textContent = fertilizerAdvice[currentLang] || fertilizerAdvice.en || '';
        if (resIrrigation) resIrrigation.textContent = irrigationAdvice[currentLang] || irrigationAdvice.en || '';
        if (resSoilImprove) resSoilImprove.textContent = soilAdvice[currentLang] || soilAdvice.en || '';
        if (resIdealWeather) resIdealWeather.textContent = weatherAdvice[currentLang] || weatherAdvice.en || '';
        if (resEstimatedIncome) resEstimatedIncome.textContent = incomeAdvice[currentLang] || incomeAdvice.en || '';

        // Show print report button when a prediction is available
        const predictionId = data.prediction_id || data._id;
        if (printReportBtn) {
            if (predictionId) {
                printReportBtn.style.display = 'inline-flex';
                printReportBtn.onclick = () => window.open(`/report/${predictionId}`, '_blank');
            } else {
                printReportBtn.style.display = 'none';
            }
        }

        showPredictionResult();
        resultCard.removeAttribute('hidden');
        resultCard.classList.remove('result-pop');
        void resultCard.offsetWidth;
        resultCard.classList.add('show', 'result-pop');
        if (predictorGrid) predictorGrid.classList.add('active-result');

        resultCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    if (predictorForm) predictorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Extract inputs
        const n = parseFloat(document.getElementById('input-n').value);
        const p = parseFloat(document.getElementById('input-p').value);
        const k = parseFloat(document.getElementById('input-k').value);
        const temp = parseFloat(document.getElementById('input-temp').value);
        const humidity = parseFloat(document.getElementById('input-humidity').value);
        const ph = parseFloat(phInput.value);
        const rainfall = parseFloat(document.getElementById('input-rainfall').value);

        // Validation
        if (isNaN(n) || n < 0 || n > 250 ||
            isNaN(p) || p < 0 || p > 250 ||
            isNaN(k) || k < 0 || k > 300 ||
            isNaN(temp) || temp < 0 || temp > 60 ||
            isNaN(humidity) || humidity < 0 || humidity > 100 ||
            isNaN(ph) || ph < 0 || ph > 14 ||
            isNaN(rainfall) || rainfall < 0 || rainfall > 500) {
            
            alert(translations[currentLang]['validation_err']);
            return;
        }

        // Show loading overlay
        loadingOverlay.classList.add('show');

        // Delay artificially by 1.2s to show gorgeous futuristic spinner animation
        setTimeout(async () => {
            try {
                const res = await fetch('/api/predict', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        N: n, P: p, K: k,
                        temperature: temp, humidity: humidity, ph: ph, rainfall: rainfall
                    })
                });
                
                const data = await res.json();
                
                if (res.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                if (data.success) {
                    lastPredictionResult = data;
                    renderPredictionResult(data);
                    // Reload dashboard to reflect new record immediately
                    fetchDashboardData();
                } else {
                    alert(data.error || translations[currentLang]['api_err']);
                }
            } catch (error) {
                console.error("Prediction API failed:", error);
                alert(translations[currentLang]['api_err']);
            } finally {
                loadingOverlay.classList.remove('show');
            }
        }, 1200);
    });

    // --- Floating Farmer Chatbot Panel (closed until message icon clicked) ---
    function openChat() {
        if (!chatWindow) return;
        chatWindow.classList.add('show');
        chatWindow.setAttribute('aria-hidden', 'false');
        if (chatBubble) chatBubble.setAttribute('aria-expanded', 'true');
        if (chatInput) chatInput.focus();
    }

    function closeChat() {
        if (!chatWindow) return;
        chatWindow.classList.remove('show');
        chatWindow.setAttribute('aria-hidden', 'true');
        if (chatBubble) chatBubble.setAttribute('aria-expanded', 'false');
    }

    if (chatWindow) {
        chatWindow.classList.remove('show', 'reveal-on-scroll', 'revealed');
        chatWindow.setAttribute('aria-hidden', 'true');
    }
    if (chatBubble) chatBubble.setAttribute('aria-expanded', 'false');

    if (chatBubble) {
        chatBubble.addEventListener('click', (e) => {
            e.stopPropagation();
            if (chatWindow && chatWindow.classList.contains('show')) {
                closeChat();
            } else {
                openChat();
            }
        });
    }

    if (chatClose) {
        chatClose.addEventListener('click', (e) => {
            e.stopPropagation();
            closeChat();
        });
    }

    document.addEventListener('click', (e) => {
        if (!chatWindow || !chatWindow.classList.contains('show')) return;
        const container = document.querySelector('.chat-container');
        if (container && !container.contains(e.target)) {
            closeChat();
        }
    });

    // Render chatbot messages
    function appendChatMessage(sender, text) {
        if (!chatMessages) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = `message-bubble ${sender}`;
        msgDiv.textContent = text;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendChatQuery(message) {
        if (!message) return;
        
        // Append user query
        appendChatMessage('user', message);
        chatInput.value = '';

        // Typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message-bubble bot typing';
        typingIndicator.textContent = '...';
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });
            const data = await res.json();
            
            // Remove typing indicator
            typingIndicator.remove();
            
            if (data.success) {
                appendChatMessage('bot', data.reply[currentLang]);
            } else {
                appendChatMessage('bot', currentLang === 'en' ? "Error connecting to agricultural agent." : "ಕೃಷಿ ಏಜೆಂಟ್‌ಗೆ ಸಂಪರ್ಕಿಸಲು ದೋಷವಾಗಿದೆ.");
            }
        } catch (error) {
            typingIndicator.remove();
            console.error("Chat API failed:", error);
            appendChatMessage('bot', currentLang === 'en' ? "Failed to send message." : "ಸಂದೇಶ ಕಳುಹಿಸಲು ವಿಫಲವಾಗಿದೆ.");
        }
    }

    if (chatSendBtn) {
        chatSendBtn.addEventListener('click', () => {
            const msg = chatInput ? chatInput.value.trim() : '';
            if (msg) sendChatQuery(msg);
        });
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const msg = chatInput.value.trim();
                if (msg) sendChatQuery(msg);
            }
        });
    }

    // Hook quick-reply tags
    if (quickReplies && quickReplies.length) {
        quickReplies.forEach(tag => {
            tag.addEventListener('click', () => {
                const queryKey = tag.getAttribute('data-query');
                const translationKey = `qr_${queryKey}`;
                const queryText = translations[currentLang][translationKey] || tag.textContent;
                sendChatQuery(queryText);
            });
        });
    }

    // --- Dashboard Analytics & Charts ---
    async function fetchDashboardData() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.success) {
                predictionsHistoryData = data.history;
                
                // Calculate and render stats
                renderGlobalStats(predictionsHistoryData);
                
                // Render List
                renderHistoryList();

                // Render Chart
                renderChart(predictionsHistoryData);
            }
        } catch (err) {
            console.error("Failed to query dashboard database:", err);
        }
    }

    function renderGlobalStats(records) {
        const valTotal = document.getElementById('val-total');
        if (!valTotal) return;
        const totalCount = records.length;
        valTotal.textContent = totalCount;

        const valPh = document.getElementById('val-ph');
        const valAcidic = document.getElementById('val-acidic');
        const valIdeal = document.getElementById('val-ideal');

        if (totalCount === 0) {
            if (valPh) valPh.textContent = '0.0';
            if (valAcidic) valAcidic.textContent = '0%';
            if (valIdeal) valIdeal.textContent = '0%';
            return;
        }

        // Average pH
        const avgPh = records.reduce((sum, r) => sum + r.ph, 0) / totalCount;
        if (valPh) valPh.textContent = avgPh.toFixed(1);

        // Acidic & Ideal ratios
        const acidicCount = records.filter(r => r.ph < 6.0).length;
        const idealCount = records.filter(r => r.ph >= 6.0 && r.ph <= 7.5).length;
        
        if (valAcidic) valAcidic.textContent = `${Math.round((acidicCount / totalCount) * 100)}%`;
        if (valIdeal) valIdeal.textContent = `${Math.round((idealCount / totalCount) * 100)}%`;
    }

    function renderHistoryList() {
        const container = document.getElementById('history-list-container');
        if (!container) return;
        container.innerHTML = '';
        
        if (predictionsHistoryData.length === 0) {
            container.innerHTML = `<div style="text-align:center; padding: 2rem; color:var(--text-muted);">No records found</div>`;
            return;
        }

        // Show recent 12 logs
        const recentLogs = predictionsHistoryData.slice(0, 12);
        recentLogs.forEach(r => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'history-item';
            
            const cropEn = r.recommended_crop;
            const localizedCrop = currentLang === 'en' ? cropEn : (cropTranslations[cropEn] || cropEn);
            
            // Format time
            let timeStr = "";
            try {
                const date = new Date(r.timestamp);
                timeStr = date.toLocaleDateString(currentLang === 'en' ? 'en-US' : 'kn-IN', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch(e) {
                timeStr = r.timestamp;
            }

            itemDiv.innerHTML = `
                <div>
                    <span class="history-crop">${localizedCrop}</span>
                    <span class="history-ph" style="margin-left: 10px;">(pH: ${r.ph})</span>
                </div>
                <span class="history-time">${timeStr}</span>
            `;
            itemDiv.style.cursor = 'pointer';
            itemDiv.addEventListener('click', () => {
                lastPredictionResult = r;
                renderPredictionResult(r);
            });
            container.appendChild(itemDiv);
        });
    }

    function renderChart(records) {
        const chartEl = document.getElementById('prediction-chart');
        if (!chartEl) return;

        // Group crops by count
        const counts = {};
        records.forEach(r => {
            const cropEn = r.recommended_crop;
            const localizedCrop = currentLang === 'en' ? cropEn : (cropTranslations[cropEn] || cropEn);
            counts[localizedCrop] = (counts[localizedCrop] || 0) + 1;
        });

        const labels = Object.keys(counts);
        const dataVals = Object.values(counts);

        const ctx = chartEl.getContext('2d');
        
        if (predictionChartInstance) {
            predictionChartInstance.destroy();
        }

        const colors = [
            '#00ffa3', '#00d4ff', '#a3e635', '#fbbf24', '#34d399',
            '#6ee7b7', '#22d3ee', '#4ade80', '#fcd34d', '#2dd4bf'
        ];
        const isLight = currentTheme === 'light';
        const tickColor = isLight ? '#1e4d3a' : '#94b8a8';
        const gridColor = isLight ? 'rgba(5, 150, 105, 0.12)' : 'rgba(0, 255, 163, 0.08)';

        const gradientFills = labels.map((_, i) => {
            const g = ctx.createLinearGradient(0, 0, 0, 280);
            const c = colors[i % colors.length];
            g.addColorStop(0, c);
            g.addColorStop(1, isLight ? 'rgba(5, 150, 105, 0.25)' : 'rgba(0, 255, 163, 0.08)');
            return g;
        });

        predictionChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: currentLang === 'en' ? 'Crop Count' : 'ಬೆಳೆ ಸಂಖ್ಯೆ',
                    data: dataVals,
                    backgroundColor: gradientFills,
                    borderColor: colors.slice(0, labels.length),
                    borderWidth: 1,
                    borderRadius: 10,
                    borderSkipped: false,
                    hoverBackgroundColor: colors.slice(0, labels.length),
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 900,
                    easing: 'easeOutQuart',
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: isLight ? 'rgba(255,255,255,0.95)' : 'rgba(8, 20, 32, 0.92)',
                        titleColor: isLight ? '#0a1628' : '#00ffa3',
                        bodyColor: isLight ? '#1e4d3a' : '#e8fff4',
                        borderColor: 'rgba(0, 255, 163, 0.35)',
                        borderWidth: 1,
                        padding: 12,
                        cornerRadius: 10,
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0, color: tickColor, font: { family: "'Exo 2', sans-serif" } },
                        grid: { color: gridColor },
                    },
                    x: {
                        ticks: { color: tickColor, font: { family: "'Exo 2', sans-serif", size: 11 } },
                        grid: { display: false },
                    },
                },
            },
        });
    }

    // Call dashboard loader only if dashboard elements exist
    if (document.getElementById('history-list-container') || document.getElementById('prediction-chart')) {
        fetchDashboardData();
    }

    // Trigger basic multilingual translation setup on load (based on saved preferences)
    const savedLang = localStorage.getItem('lang') || 'en';
    applyLocalization(savedLang);
});
