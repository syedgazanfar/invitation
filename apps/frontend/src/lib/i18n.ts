/**
 * Landing page copy in English, Hindi and Marathi.
 * Every language must have exactly the same keys (enforced by i18n.test.ts).
 */

export const LOCALES = ['en', 'hi', 'mr'] as const;
export type Locale = (typeof LOCALES)[number];

export function localePath(locale: Locale): string {
  return locale === 'en' ? '/' : `/${locale}`;
}

const en = {
  langName: 'English',
  meta: {
    title: 'Invvite · Digital Invitations for Weddings, Birthdays & Festivals',
    description:
      'Elegant digital invitations for weddings, engagements, birthdays and festivals, designed for you and shared as one WhatsApp link.',
  },
  nav: {
    occasions: 'Occasions',
    how: 'How it works',
    faq: 'FAQ',
    whatsapp: 'WhatsApp',
    enquire: 'Enquire',
    language: 'Language',
  },
  hero: {
    eyebrow: 'Digital invitations · Designed in India',
    titleLead: 'Invitations worth',
    titleEm: 'opening.',
    body: 'We design elegant digital invitations for weddings, engagements, birthdays and festivals. Your guests open them from a single WhatsApp link, are welcomed by name, and RSVP in a tap.',
    ctaPrimary: 'Plan my invitation',
    ctaWhatsapp: 'Chat on WhatsApp',
    bullets: ['Shared as one link', 'No app for guests', 'RSVPs in one place'],
  },
  mockup: {
    together: 'Together with their families',
    bride: 'Ananya',
    groom: 'Rohan',
    date: 'Sunday, 14 February 2027',
    venue: 'The Leela Palace, Udaipur',
    rsvp: 'RSVP',
    directions: 'Directions',
    welcome: 'Welcome, Priya',
    saveTheDate: 'Save the Date',
    saveTheDateNumbers: '14 · 02 · 2027',
    newRsvp: 'New RSVP',
    attending: 'Priya Sharma · Attending',
  },
  occasions: {
    eyebrow: 'Occasions',
    title: 'For every celebration worth gathering for',
    intro: 'Each invitation is designed around your event and your family, not picked from a generic template.',
    items: [
      { title: 'Weddings', text: 'Haldi, mehendi, sangeet and the big day, in one invitation or a set.' },
      { title: 'Engagement & Roka', text: 'Share the announcement with family near and far.' },
      { title: 'Birthdays', text: 'First birthdays, milestone birthdays and surprise parties.' },
      { title: 'Festivals & Pujas', text: 'Diwali, Eid, griha pravesh, naamkaran and satyanarayan puja.' },
      { title: 'Anniversaries', text: 'Silver and golden jubilees and special celebrations.' },
      { title: 'Corporate & Social', text: 'Launches, annual days and community gatherings.' },
    ],
  },
  included: {
    eyebrow: 'Every invitation includes',
    title: 'Thoughtful for you, effortless for your guests',
    intro: 'Guests feel personally invited. You know exactly who is coming.',
    items: [
      { title: 'Opens from WhatsApp', text: 'One link, no app to download. Works on any phone.' },
      { title: 'Personal welcome', text: 'Each guest is greeted by name when they open it.' },
      { title: 'Venue & directions', text: 'Address and a one-tap Google Maps link.' },
      { title: 'RSVP tracking', text: 'See who opened the invitation and who is attending.' },
      { title: 'Your photos & message', text: 'A banner photo, gallery and a note in your own words.' },
      { title: 'Guest list export', text: 'Download everyone who responded as a spreadsheet.' },
    ],
  },
  process: {
    eyebrow: 'How it works',
    title: 'From first message to RSVPs',
    steps: [
      { title: 'Tell us about your event', text: 'Fill in the short form or message us on WhatsApp with the date and occasion.' },
      { title: 'We design it with you', text: 'Choose a design; we add names, venue, photos and your message, and refine it with you.' },
      { title: 'Share one link', text: 'Send the link to your guests on WhatsApp and watch the RSVPs come in.' },
    ],
  },
  enquiry: {
    eyebrow: 'Enquire',
    title: "Let's create your invitation",
    body: "Leave your name, WhatsApp number and event date. We'll message you on WhatsApp to understand your event and share designs.",
    preferTalk: 'Prefer to talk now?',
    nameLabel: 'Your name',
    namePlaceholder: 'Full name',
    phoneLabel: 'WhatsApp number',
    phoneHint: "We'll reply on this number.",
    dateLabel: 'Date of event',
    optional: '(optional)',
    submit: 'Send enquiry',
    sending: 'Sending…',
    privacy: 'We only use your number to reply to this enquiry.',
    thanksTitle: 'Thank you',
    thanksBody: "We've received your enquiry and will contact you on WhatsApp shortly.",
    sendAnother: 'Send another enquiry',
  },
  errors: {
    name: 'Please enter your name.',
    phone: 'Please enter a valid WhatsApp number.',
    datePast: "The event date can't be in the past.",
    network: "Your enquiry couldn't be sent. Please check your internet connection and try again, or message us on WhatsApp.",
    tooMany: 'You have already sent a few enquiries. Please message us on WhatsApp instead.',
    generic: 'Something went wrong. Please try again or message us on WhatsApp.',
  },
  faq: {
    eyebrow: 'FAQ',
    title: 'Questions, answered',
    items: [
      {
        q: 'How do my guests receive the invitation?',
        a: 'You get a single link. Share it on WhatsApp, SMS, email or social media. Guests open it in their phone browser; nothing to install.',
      },
      {
        q: 'Can I see who has opened it?',
        a: 'Yes. Your dashboard shows each guest who opened the invitation and their RSVP, and lets you download the list.',
      },
      {
        q: 'How long does the link stay active?',
        a: 'Your link is active for 15 days from the day it goes live. If you need it for longer, tell us when you enquire.',
      },
      {
        q: 'Can you match our wedding colours or theme?',
        a: 'Yes. Share your colours, card design or inspiration on WhatsApp and we will tailor the invitation to it.',
      },
      {
        q: 'Can I make changes after it is shared?',
        a: 'Details like the venue, time and message can be updated, and guests always see the latest version on the same link.',
      },
    ],
  },
  footer: {
    tagline: 'Digital invitations for weddings, celebrations and festivals.',
    rights: 'All rights reserved.',
  },
  whatsappMessage: 'Hi! I would like to know more about your digital invitations.',
};

export type LandingCopy = typeof en;

const hi: LandingCopy = {
  langName: 'हिंदी',
  meta: {
    title: 'Invvite · शादी, जन्मदिन और त्योहारों के लिए डिजिटल निमंत्रण',
    description:
      'शादी, सगाई, जन्मदिन और त्योहारों के लिए सुंदर डिजिटल निमंत्रण, आपके लिए डिज़ाइन किए गए और एक WhatsApp लिंक से शेयर होने वाले।',
  },
  nav: {
    occasions: 'अवसर',
    how: 'कैसे काम करता है',
    faq: 'सवाल-जवाब',
    whatsapp: 'WhatsApp',
    enquire: 'पूछताछ करें',
    language: 'भाषा',
  },
  hero: {
    eyebrow: 'डिजिटल निमंत्रण · भारत में डिज़ाइन',
    titleLead: 'निमंत्रण, जिसे',
    titleEm: 'खोलने का मन करे।',
    body: 'हम शादी, सगाई, जन्मदिन और त्योहारों के लिए सुंदर डिजिटल निमंत्रण डिज़ाइन करते हैं। मेहमान इन्हें एक WhatsApp लिंक से खोलते हैं, उनका स्वागत उनके नाम से होता है, और वे एक टैप में RSVP कर देते हैं।',
    ctaPrimary: 'मेरा निमंत्रण बनवाएँ',
    ctaWhatsapp: 'WhatsApp पर बात करें',
    bullets: ['एक ही लिंक से शेयर', 'मेहमानों को कोई ऐप नहीं चाहिए', 'सारे RSVP एक जगह'],
  },
  mockup: {
    together: 'शुभ विवाह',
    bride: 'अनन्या',
    groom: 'रोहन',
    date: 'रविवार, 14 फ़रवरी 2027',
    venue: 'द लीला पैलेस, उदयपुर',
    rsvp: 'RSVP',
    directions: 'रास्ता देखें',
    welcome: 'स्वागत है, प्रिया',
    saveTheDate: 'तारीख़ याद रखें',
    saveTheDateNumbers: '१४ · ०२ · २०२७',
    newRsvp: 'नया RSVP',
    attending: 'प्रिया शर्मा · आ रही हैं',
  },
  occasions: {
    eyebrow: 'अवसर',
    title: 'हर उस जश्न के लिए, जिसमें अपने साथ हों',
    intro: 'हर निमंत्रण आपके कार्यक्रम और परिवार को ध्यान में रखकर बनाया जाता है, किसी आम टेम्पलेट से नहीं।',
    items: [
      { title: 'शादी', text: 'हल्दी, मेहंदी, संगीत और शादी का दिन, एक निमंत्रण में या पूरे सेट में।' },
      { title: 'सगाई और रोका', text: 'दूर-पास के सभी परिवारजनों तक खुशख़बरी पहुँचाएँ।' },
      { title: 'जन्मदिन', text: 'पहला जन्मदिन, ख़ास पड़ाव वाले जन्मदिन और सरप्राइज़ पार्टियाँ।' },
      { title: 'त्योहार और पूजा', text: 'दिवाली, ईद, गृह प्रवेश, नामकरण और सत्यनारायण पूजा।' },
      { title: 'सालगिरह', text: 'शादी की 25वीं, 50वीं सालगिरह और ख़ास समारोह।' },
      { title: 'कॉर्पोरेट और सामाजिक', text: 'लॉन्च, वार्षिक समारोह और सामुदायिक कार्यक्रम।' },
    ],
  },
  included: {
    eyebrow: 'हर निमंत्रण में शामिल',
    title: 'आपके लिए सोच-समझकर, मेहमानों के लिए बेहद आसान',
    intro: 'मेहमानों को लगता है कि उन्हें ख़ास तौर पर बुलाया गया है। और आपको पता रहता है कि कौन आ रहा है।',
    items: [
      { title: 'WhatsApp से खुलता है', text: 'एक लिंक, कोई ऐप डाउनलोड नहीं। किसी भी फ़ोन पर चलता है।' },
      { title: 'व्यक्तिगत स्वागत', text: 'निमंत्रण खोलते ही हर मेहमान का स्वागत उसके नाम से होता है।' },
      { title: 'स्थान और रास्ता', text: 'पता और एक टैप में Google Maps लिंक।' },
      { title: 'RSVP ट्रैकिंग', text: 'देखें किसने निमंत्रण खोला और कौन आ रहा है।' },
      { title: 'आपकी तस्वीरें और संदेश', text: 'बैनर फ़ोटो, गैलरी और आपके अपने शब्दों में संदेश।' },
      { title: 'मेहमानों की सूची', text: 'जवाब देने वाले सभी मेहमानों की सूची स्प्रेडशीट में डाउनलोड करें।' },
    ],
  },
  process: {
    eyebrow: 'कैसे काम करता है',
    title: 'पहले संदेश से RSVP तक',
    steps: [
      { title: 'अपने कार्यक्रम के बारे में बताएँ', text: 'छोटा फ़ॉर्म भरें या WhatsApp पर तारीख़ और अवसर के साथ संदेश भेजें।' },
      { title: 'हम आपके साथ डिज़ाइन करते हैं', text: 'डिज़ाइन चुनें; हम नाम, स्थान, तस्वीरें और आपका संदेश जोड़कर आपके साथ उसे निखारते हैं।' },
      { title: 'एक लिंक शेयर करें', text: 'मेहमानों को WhatsApp पर लिंक भेजें और RSVP आते देखें।' },
    ],
  },
  enquiry: {
    eyebrow: 'पूछताछ',
    title: 'आइए, आपका निमंत्रण बनाएँ',
    body: 'अपना नाम, WhatsApp नंबर और कार्यक्रम की तारीख़ दें। हम WhatsApp पर संपर्क करके आपके कार्यक्रम को समझेंगे और डिज़ाइन भेजेंगे।',
    preferTalk: 'अभी बात करना चाहते हैं?',
    nameLabel: 'आपका नाम',
    namePlaceholder: 'पूरा नाम',
    phoneLabel: 'WhatsApp नंबर',
    phoneHint: 'हम इसी नंबर पर जवाब देंगे।',
    dateLabel: 'कार्यक्रम की तारीख़',
    optional: '(वैकल्पिक)',
    submit: 'पूछताछ भेजें',
    sending: 'भेजा जा रहा है…',
    privacy: 'आपका नंबर केवल इस पूछताछ का जवाब देने के लिए इस्तेमाल होगा।',
    thanksTitle: 'धन्यवाद',
    thanksBody: 'आपकी पूछताछ हमें मिल गई है। हम जल्द ही WhatsApp पर आपसे संपर्क करेंगे।',
    sendAnother: 'एक और पूछताछ भेजें',
  },
  errors: {
    name: 'कृपया अपना नाम लिखें।',
    phone: 'कृपया सही WhatsApp नंबर लिखें।',
    datePast: 'कार्यक्रम की तारीख़ बीती हुई नहीं हो सकती।',
    network: 'पूछताछ नहीं भेजी जा सकी। कृपया इंटरनेट कनेक्शन जाँचकर फिर कोशिश करें, या WhatsApp पर संदेश भेजें।',
    tooMany: 'आप पहले ही कुछ पूछताछ भेज चुके हैं। कृपया WhatsApp पर संदेश भेजें।',
    generic: 'कुछ गड़बड़ हो गई। कृपया फिर कोशिश करें या WhatsApp पर संदेश भेजें।',
  },
  faq: {
    eyebrow: 'सवाल-जवाब',
    title: 'आपके सवाल, हमारे जवाब',
    items: [
      {
        q: 'मेहमानों तक निमंत्रण कैसे पहुँचता है?',
        a: 'आपको एक लिंक मिलता है। उसे WhatsApp, SMS, ईमेल या सोशल मीडिया पर शेयर करें। मेहमान इसे अपने फ़ोन के ब्राउज़र में खोलते हैं, कुछ इंस्टॉल नहीं करना पड़ता।',
      },
      {
        q: 'क्या पता चलता है कि निमंत्रण किसने खोला?',
        a: 'हाँ। आपके डैशबोर्ड पर हर उस मेहमान का नाम और RSVP दिखता है जिसने निमंत्रण खोला, और आप सूची डाउनलोड भी कर सकते हैं।',
      },
      {
        q: 'लिंक कितने दिन चालू रहता है?',
        a: 'लिंक लाइव होने के दिन से 15 दिन तक चालू रहता है। ज़्यादा समय चाहिए तो पूछताछ करते समय बताएँ।',
      },
      {
        q: 'क्या आप हमारी शादी के रंग या थीम से मिलान कर सकते हैं?',
        a: 'हाँ। WhatsApp पर अपने रंग, कार्ड का डिज़ाइन या पसंद के उदाहरण भेजें, हम निमंत्रण उसी के अनुसार बनाएँगे।',
      },
      {
        q: 'शेयर करने के बाद क्या बदलाव कर सकते हैं?',
        a: 'स्थान, समय और संदेश जैसी जानकारी बदली जा सकती है, और मेहमानों को उसी लिंक पर हमेशा नया संस्करण दिखता है।',
      },
    ],
  },
  footer: {
    tagline: 'शादी, उत्सव और त्योहारों के लिए डिजिटल निमंत्रण।',
    rights: 'सर्वाधिकार सुरक्षित।',
  },
  whatsappMessage: 'नमस्ते! मुझे आपके डिजिटल निमंत्रणों के बारे में जानकारी चाहिए।',
};

const mr: LandingCopy = {
  langName: 'मराठी',
  meta: {
    title: 'Invvite · लग्न, वाढदिवस आणि सणांसाठी डिजिटल निमंत्रणे',
    description:
      'लग्न, साखरपुडा, वाढदिवस आणि सणांसाठी सुंदर डिजिटल निमंत्रणे, तुमच्यासाठी डिझाइन केलेली आणि एका WhatsApp लिंकने शेअर होणारी.',
  },
  nav: {
    occasions: 'प्रसंग',
    how: 'कसे काम करते',
    faq: 'प्रश्नोत्तरे',
    whatsapp: 'WhatsApp',
    enquire: 'चौकशी करा',
    language: 'भाषा',
  },
  hero: {
    eyebrow: 'डिजिटल निमंत्रणे · भारतात डिझाइन केलेली',
    titleLead: 'निमंत्रण, जे',
    titleEm: 'उघडावेसे वाटेल.',
    body: 'आम्ही लग्न, साखरपुडा, वाढदिवस आणि सणांसाठी सुंदर डिजिटल निमंत्रणे डिझाइन करतो. पाहुणे ती एका WhatsApp लिंकवरून उघडतात, त्यांचे नावाने स्वागत होते आणि ते एका टॅपमध्ये RSVP करतात.',
    ctaPrimary: 'माझे निमंत्रण तयार करा',
    ctaWhatsapp: 'WhatsApp वर बोला',
    bullets: ['एकाच लिंकने शेअर', 'पाहुण्यांना कोणतेही अ‍ॅप नको', 'सर्व RSVP एकाच ठिकाणी'],
  },
  mockup: {
    together: 'शुभ विवाह',
    bride: 'अनन्या',
    groom: 'रोहन',
    date: 'रविवार, १४ फेब्रुवारी २०२७',
    venue: 'द लीला पॅलेस, उदयपूर',
    rsvp: 'RSVP',
    directions: 'दिशा पाहा',
    welcome: 'स्वागत, प्रिया',
    saveTheDate: 'तारीख लक्षात ठेवा',
    saveTheDateNumbers: '१४ · ०२ · २०२७',
    newRsvp: 'नवीन RSVP',
    attending: 'प्रिया शर्मा · येत आहेत',
  },
  occasions: {
    eyebrow: 'प्रसंग',
    title: 'आप्तेष्टांसोबत साजऱ्या होणाऱ्या प्रत्येक आनंदासाठी',
    intro: 'प्रत्येक निमंत्रण तुमच्या कार्यक्रमाचा आणि कुटुंबाचा विचार करून डिझाइन केले जाते, कोणत्याही सामान्य टेम्पलेटमधून निवडलेले नाही.',
    items: [
      { title: 'लग्न', text: 'हळद, मेहेंदी, संगीत आणि लग्नाचा दिवस, एका निमंत्रणात किंवा संपूर्ण संचात.' },
      { title: 'साखरपुडा', text: 'जवळच्या आणि दूरच्या सर्व नातेवाईकांपर्यंत आनंदाची बातमी पोहोचवा.' },
      { title: 'वाढदिवस', text: 'पहिला वाढदिवस, खास टप्प्यांचे वाढदिवस आणि सरप्राइज पार्ट्या.' },
      { title: 'सण आणि पूजा', text: 'दिवाळी, ईद, गृहप्रवेश, बारसे आणि सत्यनारायण पूजा.' },
      { title: 'लग्नाचे वाढदिवस', text: 'लग्नाचा २५ वा, ५० वा वाढदिवस आणि खास सोहळे.' },
      { title: 'कॉर्पोरेट आणि सामाजिक', text: 'लाँच, वार्षिक सोहळे आणि सामाजिक कार्यक्रम.' },
    ],
  },
  included: {
    eyebrow: 'प्रत्येक निमंत्रणात समाविष्ट',
    title: 'तुमच्यासाठी विचारपूर्वक, पाहुण्यांसाठी अगदी सोपे',
    intro: 'पाहुण्यांना खास आमंत्रित केल्यासारखे वाटते. आणि कोण येत आहे हे तुम्हाला नेमके कळते.',
    items: [
      { title: 'WhatsApp वरून उघडते', text: 'एक लिंक, कोणतेही अ‍ॅप डाउनलोड नाही. कोणत्याही फोनवर चालते.' },
      { title: 'वैयक्तिक स्वागत', text: 'निमंत्रण उघडताच प्रत्येक पाहुण्याचे नावाने स्वागत होते.' },
      { title: 'ठिकाण आणि दिशा', text: 'पत्ता आणि एका टॅपमध्ये Google Maps लिंक.' },
      { title: 'RSVP ट्रॅकिंग', text: 'कोणी निमंत्रण उघडले आणि कोण येत आहे ते पाहा.' },
      { title: 'तुमचे फोटो आणि संदेश', text: 'बॅनर फोटो, गॅलरी आणि तुमच्या शब्दांतील संदेश.' },
      { title: 'पाहुण्यांची यादी', text: 'प्रतिसाद दिलेल्या सर्व पाहुण्यांची यादी स्प्रेडशीटमध्ये डाउनलोड करा.' },
    ],
  },
  process: {
    eyebrow: 'कसे काम करते',
    title: 'पहिल्या संदेशापासून RSVP पर्यंत',
    steps: [
      { title: 'तुमच्या कार्यक्रमाबद्दल सांगा', text: 'छोटा फॉर्म भरा किंवा WhatsApp वर तारीख आणि प्रसंगासह संदेश पाठवा.' },
      { title: 'आम्ही तुमच्यासोबत डिझाइन करतो', text: 'डिझाइन निवडा; आम्ही नावे, ठिकाण, फोटो आणि तुमचा संदेश जोडून तुमच्यासोबत ते अधिक सुंदर करतो.' },
      { title: 'एक लिंक शेअर करा', text: 'पाहुण्यांना WhatsApp वर लिंक पाठवा आणि RSVP येताना पाहा.' },
    ],
  },
  enquiry: {
    eyebrow: 'चौकशी',
    title: 'चला, तुमचे निमंत्रण तयार करूया',
    body: 'तुमचे नाव, WhatsApp नंबर आणि कार्यक्रमाची तारीख द्या. आम्ही WhatsApp वर संपर्क करून तुमचा कार्यक्रम समजून घेऊ आणि डिझाइन पाठवू.',
    preferTalk: 'आत्ताच बोलायचे आहे?',
    nameLabel: 'तुमचे नाव',
    namePlaceholder: 'पूर्ण नाव',
    phoneLabel: 'WhatsApp नंबर',
    phoneHint: 'आम्ही याच नंबरवर उत्तर देऊ.',
    dateLabel: 'कार्यक्रमाची तारीख',
    optional: '(ऐच्छिक)',
    submit: 'चौकशी पाठवा',
    sending: 'पाठवत आहे…',
    privacy: 'तुमचा नंबर फक्त या चौकशीला उत्तर देण्यासाठी वापरला जाईल.',
    thanksTitle: 'धन्यवाद',
    thanksBody: 'तुमची चौकशी आम्हाला मिळाली आहे. आम्ही लवकरच WhatsApp वर तुमच्याशी संपर्क साधू.',
    sendAnother: 'आणखी एक चौकशी पाठवा',
  },
  errors: {
    name: 'कृपया तुमचे नाव लिहा.',
    phone: 'कृपया योग्य WhatsApp नंबर लिहा.',
    datePast: 'कार्यक्रमाची तारीख भूतकाळातील असू शकत नाही.',
    network: 'चौकशी पाठवता आली नाही. कृपया इंटरनेट कनेक्शन तपासून पुन्हा प्रयत्न करा, किंवा WhatsApp वर संदेश पाठवा.',
    tooMany: 'तुम्ही आधीच काही चौकशा पाठवल्या आहेत. कृपया WhatsApp वर संदेश पाठवा.',
    generic: 'काहीतरी चूक झाली. कृपया पुन्हा प्रयत्न करा किंवा WhatsApp वर संदेश पाठवा.',
  },
  faq: {
    eyebrow: 'प्रश्नोत्तरे',
    title: 'तुमचे प्रश्न, आमची उत्तरे',
    items: [
      {
        q: 'पाहुण्यांपर्यंत निमंत्रण कसे पोहोचते?',
        a: 'तुम्हाला एक लिंक मिळते. ती WhatsApp, SMS, ईमेल किंवा सोशल मीडियावर शेअर करा. पाहुणे ती त्यांच्या फोनच्या ब्राउझरमध्ये उघडतात, काहीही इन्स्टॉल करावे लागत नाही.',
      },
      {
        q: 'निमंत्रण कोणी उघडले ते मला पाहता येईल का?',
        a: 'हो. तुमच्या डॅशबोर्डवर निमंत्रण उघडणाऱ्या प्रत्येक पाहुण्याचे नाव आणि त्यांचा RSVP दिसतो, आणि तुम्ही यादी डाउनलोडही करू शकता.',
      },
      {
        q: 'लिंक किती दिवस सुरू राहते?',
        a: 'लिंक लाइव्ह झाल्यापासून १५ दिवस सुरू राहते. जास्त काळ हवी असल्यास चौकशी करताना सांगा.',
      },
      {
        q: 'तुम्ही आमच्या लग्नाच्या रंगसंगती किंवा थीमशी जुळवून देऊ शकता का?',
        a: 'हो. WhatsApp वर तुमचे रंग, पत्रिकेचे डिझाइन किंवा आवडीची उदाहरणे पाठवा, आम्ही निमंत्रण त्यानुसार तयार करू.',
      },
      {
        q: 'शेअर केल्यानंतर बदल करता येतात का?',
        a: 'ठिकाण, वेळ आणि संदेश यांसारखे तपशील बदलता येतात, आणि पाहुण्यांना त्याच लिंकवर नेहमी नवीन आवृत्ती दिसते.',
      },
    ],
  },
  footer: {
    tagline: 'लग्न, सोहळे आणि सणांसाठी डिजिटल निमंत्रणे.',
    rights: 'सर्व हक्क राखीव.',
  },
  whatsappMessage: 'नमस्कार! मला तुमच्या डिजिटल निमंत्रणांबद्दल माहिती हवी आहे.',
};

export const LANDING_COPY: Record<Locale, LandingCopy> = { en, hi, mr };
