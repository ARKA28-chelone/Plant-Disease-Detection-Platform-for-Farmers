// ---------- Hindi / English toggle ----------
// Pages are written in English; when Hindi is chosen, known text (including
// content added later by scripts) is swapped using the dictionary below.
const I18n = (function () {
  const HI = {
    // Navbar & common
    "Home": "होम", "About": "परिचय", "Plant Diseases": "पौधों के रोग", "Detection": "जाँच",
    "Dashboard": "डैशबोर्ड", "Tracker": "ट्रैकर", "Assistant": "सहायक", "Tools": "टूल्स",
    "Login": "लॉगिन", "Logout": "लॉगआउट", "Admin": "एडमिन", "Sign up": "साइन अप",
    "DBMS Project – Plant Disease Detection Using Machine Learning": "डीबीएमएस प्रोजेक्ट – मशीन लर्निंग द्वारा पौधों के रोग की पहचान",
    "Save": "सहेजें", "Cancel": "रद्द करें", "Delete": "हटाएँ", "Send": "भेजें", "Loading...": "लोड हो रहा है...",
    "Please wait...": "कृपया प्रतीक्षा करें...", "Preparing...": "तैयार हो रहा है...", "Saved": "सहेजा गया",

    // Home page
    "Plant Disease Detection Using Machine Learning": "मशीन लर्निंग द्वारा पौधों के रोग की पहचान",
    "Get Started": "शुरू करें",
    "Upload a photo of a plant leaf and let a trained ML model help identify possible diseases, so farmers can act early.":
      "पौधे की पत्ती की फ़ोटो अपलोड करें और प्रशिक्षित एमएल मॉडल को संभावित रोग पहचानने दें, ताकि किसान समय पर कदम उठा सकें।",
    "Plant diseases reduce crop yield and farmers' income. Identifying a disease by eye needs expertise and is often slow. A machine learning model can be trained on labelled leaf images to recognise disease patterns quickly.":
      "पौधों के रोग फसल की उपज और किसानों की आय घटाते हैं। आँख से रोग पहचानने के लिए विशेषज्ञता चाहिए और यह अक्सर धीमा होता है। लेबल की गई पत्तियों की फ़ोटो पर प्रशिक्षित मशीन लर्निंग मॉडल रोग के पैटर्न जल्दी पहचान सकता है।",
    "No ML model or backend is connected yet, so no prediction is made.": "पत्ती की फ़ोटो चुनें और \"रोग पहचानें\" दबाएँ।",
    "Prediction completed with high confidence using DINOv2 vision model.": "DINOv2 विज़न मॉडल द्वारा उच्च विश्वास के साथ पहचान पूरी हुई।",
    "Includes image, diagnosis and treatment plan.": "फ़ोटो, निदान और उपचार योजना शामिल है।",
    "Reports are saved to your account.": "रिपोर्ट आपके खाते में सहेजी जाती हैं।",
    "Running ML model and querying database...": "एमएल मॉडल चल रहा है और डेटाबेस से जानकारी ली जा रही है...",
    "About the Project": "प्रोजेक्ट के बारे में",
    "1. Upload": "1. अपलोड करें", "2. Predict": "2. पहचान", "3. Store & Show": "3. सहेजें और दिखाएँ",
    "The user uploads a leaf image through this web page.": "उपयोगकर्ता इस वेब पेज से पत्ती की फ़ोटो अपलोड करता है।",
    "A backend server will pass the image to the ML model.": "सर्वर फ़ोटो को एमएल मॉडल तक भेजता है।",
    "Disease details and history will come from a MySQL database.": "रोग की जानकारी और इतिहास डेटाबेस से आता है।",
    "Example diseases for the four plant categories.": "चार फसलों के कुछ सामान्य रोग।",
    "Disease Detection": "रोग की जाँच",
    "Upload a clear image of a single leaf (JPG or PNG, max 5 MB).": "एक पत्ती की साफ़ फ़ोटो अपलोड करें (JPG या PNG, अधिकतम 5 MB)।",
    "Step 1: Select the plant": "चरण 1: पौधा चुनें",
    "Step 2: Choose a leaf image": "चरण 2: पत्ती की फ़ोटो चुनें",
    "Step 3 (optional): Link to a tracked plant": "चरण 3 (वैकल्पिक): ट्रैक किए गए पौधे से जोड़ें",
    "Not linked": "जुड़ा नहीं",
    "No image selected": "कोई फ़ोटो नहीं चुनी गई",
    "Detect Disease": "रोग पहचानें", "Analyzing leaf...": "पत्ती की जाँच हो रही है...",
    "Result": "परिणाम", "Predicted disease": "अनुमानित रोग", "Confidence score": "विश्वास स्कोर",
    "Disease information": "रोग की जानकारी", "Not available yet": "अभी उपलब्ध नहीं",
    "Will be loaded from the database": "डेटाबेस से लोड होगा",
    "Pending model integration": "परिणाम की प्रतीक्षा",
    "Download PDF Report": "PDF रिपोर्ट डाउनलोड करें", "Log in to get the PDF Report": "PDF रिपोर्ट के लिए लॉगिन करें",
    "Ask the assistant": "सहायक से पूछें", "Was this prediction right?": "क्या यह पहचान सही थी?",
    "👍 Yes": "👍 हाँ", "👎 No": "👎 नहीं", "Thanks for your feedback!": "आपकी प्रतिक्रिया के लिए धन्यवाद!",
    "View all diseases →": "सभी रोग देखें →",
    "Farmer Tools": "किसान टूल्स", "Log in to save your scans and use these tools.": "अपने स्कैन सहेजने और ये टूल्स उपयोग करने के लिए लॉगिन करें।",
    "PDF Health Report": "PDF स्वास्थ्य रिपोर्ट", "Health Tracker": "स्वास्थ्य ट्रैकर", "Krishi Mitra Assistant": "कृषि मित्र सहायक",
    "Download any scan as a report with the leaf image, diagnosis and a treatment plan.": "किसी भी स्कैन को पत्ती की फ़ोटो, निदान और उपचार योजना के साथ रिपोर्ट के रूप में डाउनलोड करें।",
    "Log how your plants are doing, see their health over time and get a quick recommendation.": "अपने पौधों की स्थिति दर्ज करें, समय के साथ उनका स्वास्थ्य देखें और सुझाव पाएँ।",
    "Ask an AI assistant about diseases, pests, watering and plant care.": "रोग, कीट, सिंचाई और पौधों की देखभाल के बारे में एआई सहायक से पूछें।",
    "Try it now": "अभी आज़माएँ", "Open my scans →": "मेरे स्कैन खोलें →", "Open tracker →": "ट्रैकर खोलें →", "Ask a question →": "प्रश्न पूछें →",

    // Extra features
    "No image selected – drop a leaf photo here": "कोई फ़ोटो नहीं चुनी गई – पत्ती की फ़ोटो यहाँ छोड़ें",
    "Scanning many leaves? Try batch scan →": "कई पत्तियाँ जाँचनी हैं? बैच स्कैन आज़माएँ →",
    "Other possibilities": "अन्य संभावनाएँ", "📷 Take a photo": "📷 फ़ोटो लें",
    "Batch Scan": "बैच स्कैन", "Scan All": "सभी स्कैन करें", "Clear": "हटाएँ", "Summary": "सारांश", "Leaves": "पत्तियाँ",
    "Check up to 10 leaves at once – ideal for walking a whole field.": "एक साथ 10 पत्तियाँ तक जाँचें – पूरे खेत के लिए बढ़िया।",
    "Drop leaf photos here": "पत्तियों की फ़ोटो यहाँ छोड़ें", "Leaf": "पत्ती", "Photo check": "फ़ोटो जाँच",
    "✓ Good photo": "✓ अच्छी फ़ोटो", "Waiting": "प्रतीक्षा", "Report": "रिपोर्ट",
    "Add photos and press Scan All.": "फ़ोटो जोड़ें और \"सभी स्कैन करें\" दबाएँ।",
    "Before & After": "पहले और बाद", "Before": "पहले", "After": "बाद",
    "Compare two scans to see whether a treatment is working.": "दो स्कैन की तुलना करके देखें कि उपचार काम कर रहा है या नहीं।",
    "Compare with another scan": "दूसरे स्कैन से तुलना करें", "Compare first and latest scan →": "पहले और नए स्कैन की तुलना करें →",
    "Open full report →": "पूरी रिपोर्ट खोलें →", "You're offline": "आप ऑफ़लाइन हैं", "Try again": "फिर से कोशिश करें",

    // Login
    "Welcome back": "फिर से स्वागत है", "Create an account": "खाता बनाएँ", "Full name": "पूरा नाम",
    "Email": "ईमेल", "Password": "पासवर्ड", "Show": "दिखाएँ", "Hide": "छिपाएँ", "Create account": "खाता बनाएँ",
    "Continue without an account →": "बिना खाते के जारी रखें →",
    "Log in to save your scans and view your history.": "अपने स्कैन सहेजने और इतिहास देखने के लिए लॉगिन करें।",
    "Sign up to keep a history of every leaf you scan.": "हर स्कैन का इतिहास रखने के लिए साइन अप करें।",

    // Dashboard
    "Your Plant Health Dashboard": "आपका पौधा स्वास्थ्य डैशबोर्ड", "A quick overview of the leaves you have scanned.": "आपके स्कैन की गई पत्तियों का संक्षिप्त विवरण।",
    "Overview": "सारांश", "Total scans": "कुल स्कैन", "Diseases found": "रोग मिले", "Healthy leaves": "स्वस्थ पत्तियाँ",
    "Model accuracy": "मॉडल सटीकता", "Most scanned crop": "सबसे ज़्यादा स्कैन की गई फसल",
    "Scans by Plant": "पौधे के अनुसार स्कैन", "How many leaves of each crop you have checked.": "आपने हर फसल की कितनी पत्तियाँ जाँचीं।",
    "Recent Scans": "हाल के स्कैन", "My Scans": "मेरे स्कैन", "Click a scan to open its full report.": "पूरी रिपोर्ट देखने के लिए स्कैन पर क्लिक करें।",
    "Scan a New Leaf": "नई पत्ती स्कैन करें", "PDF Report": "PDF रिपोर्ट", "Reminders": "रिमाइंडर",
    "Search": "खोजें", "All plants": "सभी पौधे", "All diseases": "सभी रोग", "Diseases only": "केवल रोग",
    "From": "से", "To": "तक", "Clear filters": "फ़िल्टर हटाएँ", "No scans match these filters.": "इन फ़िल्टर से कोई स्कैन नहीं मिला।",
    "Export my data": "मेरा डेटा निर्यात करें", "Scans (CSV)": "स्कैन (CSV)", "Health logs (CSV)": "स्वास्थ्य लॉग (CSV)",
    "Done": "पूरा हुआ", "Due now": "अभी करना है", "Upcoming": "आने वाले",

    // Results
    "Plant Health Report": "पौधा स्वास्थ्य रिपोर्ट", "Detection Result": "जाँच परिणाम", "Plant": "पौधा", "Scanned on": "स्कैन तिथि",
    "Pathogen type": "रोगाणु प्रकार", "Symptoms": "लक्षण", "Prevention": "बचाव", "Treatments": "उपचार",
    "My Notes": "मेरे नोट्स", "Save notes": "नोट्स सहेजें", "Tracked plant": "ट्रैक किया गया पौधा", "Remind me to re-scan": "दोबारा स्कैन की याद दिलाएँ",
    "in 3 days": "3 दिन में", "in 7 days": "7 दिन में", "in 14 days": "14 दिन में", "Set reminder": "रिमाइंडर सेट करें",
    "← Back to Dashboard": "← डैशबोर्ड पर वापस", "Scan Another Leaf": "दूसरी पत्ती स्कैन करें",
    "Healthy leaf": "स्वस्थ पत्ती", "Disease detected": "रोग मिला",

    // Tracker
    "Plant Health Tracker": "पौधा स्वास्थ्य ट्रैकर", "My Plants": "मेरे पौधे", "Add a Plant": "पौधा जोड़ें", "Name": "नाम", "Crop": "फसल",
    "Add Plant": "पौधा जोड़ें", "💡 Recommendation": "💡 सुझाव", "Health over time": "समय के साथ स्वास्थ्य",
    "Log today's health": "आज का स्वास्थ्य दर्ज करें", "Overall health": "कुल स्वास्थ्य", "What did you notice / do?": "आपने क्या देखा / किया?",
    "Leaf spots": "पत्तियों पर धब्बे", "Yellowing": "पीलापन", "Wilting": "मुरझाना", "Pests": "कीट", "Watered": "पानी दिया",
    "Treated / sprayed": "उपचार / छिड़काव किया", "When": "कब", "Today": "आज", "Yesterday": "कल",
    "Notes (optional)": "नोट्स (वैकल्पिक)", "Save Log": "लॉग सहेजें", "Log history": "लॉग इतिहास",
    "Linked scans": "जुड़े हुए स्कैन", "Summary PDF": "सारांश PDF", "Remove plant": "पौधा हटाएँ", "Remind me in 7 days": "7 दिन में याद दिलाएँ",
    "▲ Improving": "▲ सुधार", "▼ Declining": "▼ गिरावट", "● Stable": "● स्थिर", "New": "नया",

    // Assistant
    "Krishi Mitra – Farmer Assistant": "कृषि मित्र – किसान सहायक", "Krishi Mitra": "कृषि मित्र", "Farmer assistant": "किसान सहायक",
    "Ask anything about crop diseases, pests, watering or plant care.": "फसल रोग, कीट, सिंचाई या पौधों की देखभाल के बारे में कुछ भी पूछें।",
    "Thinking...": "सोच रहा हूँ...",
    "Namaste! 🌱 Ask me anything about crop diseases, pests or plant care.":
      "नमस्ते! 🌱 फसल रोग, कीट या पौधों की देखभाल के बारे में कुछ भी पूछें। आप हिंदी या हिंग्लिश में पूछ सकते हैं – जवाब सरल अंग्रेज़ी में आएँगे।",
    "Namaste! 🌱 Please log in to chat with Krishi Mitra.": "नमस्ते! 🌱 कृषि मित्र से बात करने के लिए कृपया लॉगिन करें।",
    "Namaste! 🌱 I'm Krishi Mitra. I can look up diseases in our database and check your own scans and tracked plants. What would you like to know?":
      "नमस्ते! 🌱 मैं कृषि मित्र हूँ। मैं डेटाबेस में रोग खोज सकता हूँ और आपके स्कैन व पौधे देख सकता हूँ। आप हिंदी या हिंग्लिश में पूछ सकते हैं – जवाब सरल अंग्रेज़ी में आएँगे।",
    "Log in →": "लॉगिन करें →", "Open full assistant →": "पूरा सहायक खोलें →",

    // Disease library
    "Disease Library": "रोग पुस्तकालय", "Every disease our model can detect, with symptoms and treatments.": "हर रोग जिसे हमारा मॉडल पहचान सकता है, लक्षण और उपचार के साथ।",
    "Search diseases...": "रोग खोजें...", "Organic": "जैविक", "Chemical": "रासायनिक", "Cultural": "कृषि पद्धति",

    // Profile
    "My Profile": "मेरी प्रोफ़ाइल", "Account details": "खाते का विवरण", "Member since": "सदस्य कब से", "Change password": "पासवर्ड बदलें",
    "Current password": "वर्तमान पासवर्ड", "New password": "नया पासवर्ड", "Update password": "पासवर्ड अपडेट करें",
    "Delete account": "खाता हटाएँ", "Save name": "नाम सहेजें", "Your activity": "आपकी गतिविधि",
    "Tracked plants": "ट्रैक किए गए पौधे", "Health logs": "स्वास्थ्य लॉग",

    // Admin
    "Admin Overview": "एडमिन सारांश", "Users": "उपयोगकर्ता", "Scans per day": "प्रतिदिन स्कैन", "Most common diseases": "सबसे आम रोग",
    "Recent users": "हाल के उपयोगकर्ता"
  };

  const PLACEHOLDERS = {
    "Type your question...": "अपना प्रश्न लिखें...", "Ask about your crops...": "अपनी फसल के बारे में पूछें...",
    "Search diseases...": "रोग खोजें...", "Search disease, plant or notes...": "रोग, पौधा या नोट्स खोजें...",
    "e.g. Back field tomatoes": "जैसे: पीछे के खेत के टमाटर", "you@example.com": "you@example.com",
    "At least 6 characters": "कम से कम 6 अक्षर", "Write what you did or noticed...": "आपने क्या किया या देखा, लिखें..."
  };

  function getLang() {
    try { return localStorage.getItem("pc_lang") === "hi" ? "hi" : "en"; } catch (e) { return "en"; }
  }

  function translateNode(root) {
    if (getLang() !== "hi" || !root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null);
    let node;
    while ((node = walker.nextNode())) {
      const text = node.nodeValue.replace(/\s+/g, " ").trim();
      if (text && HI[text] && node.parentNode && node.parentNode.nodeName !== "SCRIPT") {
        node.nodeValue = " " + HI[text] + " ";
      }
    }
    if (root.querySelectorAll) {
      root.querySelectorAll("[placeholder]").forEach(function (el) {
        const p = el.getAttribute("placeholder");
        if (PLACEHOLDERS[p]) el.setAttribute("placeholder", PLACEHOLDERS[p]);
      });
    }
  }

  function addToggle() {
    const nav = document.querySelector(".navbar nav");
    if (!nav || nav.querySelector(".lang-toggle")) return;
    const link = document.createElement("a");
    link.href = "#";
    link.className = "lang-toggle";
    link.title = "Change language";
    link.textContent = getLang() === "hi" ? "English" : "हिंदी";
    link.addEventListener("click", function (e) {
      e.preventDefault();
      try { localStorage.setItem("pc_lang", getLang() === "hi" ? "en" : "hi"); } catch (err) { /* ignore */ }
      window.location.reload();
    });
    // Keep the login/logout links last
    const auth = nav.querySelector(".nav-auth");
    nav.insertBefore(link, auth || null);
  }

  document.addEventListener("DOMContentLoaded", function () {
    addToggle();
    if (getLang() !== "hi") return;
    document.documentElement.lang = "hi";
    translateNode(document.body);
    // Translate content that scripts add later (results, cards, chat, etc.)
    new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        m.addedNodes.forEach(function (n) {
          if (n.nodeType === 1) translateNode(n);
          else if (n.nodeType === 3 && n.parentNode) translateNode(n.parentNode);
        });
      });
    }).observe(document.body, { childList: true, subtree: true });
  });

  return { getLang: getLang, translate: translateNode };
})();
