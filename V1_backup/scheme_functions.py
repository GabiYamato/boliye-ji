"""
Scheme Functions - Pure function implementations without framework dependencies
These functions can be called by the LLM or tested independently
"""

import sys

# Try to import loguru, fall back to standard logging
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)


# ============================================================================
# FUNCTION IMPLEMENTATIONS
# ============================================================================

async def check_eligibility(function_name, tool_call_id, args, llm, context, result_callback):
    """
    Function 1: Check eligibility for government schemes
    Returns Hindi text with eligibility information
    """
    logger.info(f"🔍 Checking eligibility with args: {args}")
    
    category = args.get("category", "सामान्य")
    income = args.get("annual_income", 0)
    education_level = args.get("education_level", "माध्यमिक")
    
    # Dummy eligibility logic
    eligible_schemes = []
    
    if income < 250000:
        eligible_schemes.append("प्री-मैट्रिक स्कॉलरशिप योजना")
    
    if income < 500000:
        eligible_schemes.append("पोस्ट-मैट्रिक स्कॉलरशिप योजना")
        if category in ["अनुसूचित जाति", "अनुसूचित जनजाति"]:
            eligible_schemes.append("एस सी एस टी छात्रवृत्ति योजना")
    
    if education_level in ["स्नातक", "स्नातकोत्तर"]:
        eligible_schemes.append("मेरिट कम मीन्स स्कॉलरशिप")
    
    # Create detailed Hindi response
    if eligible_schemes:
        response_text = f"आपकी पात्रता के अनुसार, आप निम्नलिखित योजनाओं के लिए आवेदन कर सकते हैं: "
        response_text += ", ".join(eligible_schemes)
        response_text += "। आपकी वार्षिक आय {0} रुपये है और आप {1} श्रेणी में हैं।".format(income, category)
    else:
        response_text = "माफ़ कीजिये, आपके दिए गए विवरण के अनुसार कोई योजना उपलब्ध नहीं है। कृपया अपनी जानकारी की जांच करें।"
    
    result = {
        "eligible": len(eligible_schemes) > 0,
        "schemes": eligible_schemes,
        "message": response_text,
        "category": category,
        "income": income
    }
    
    await result_callback(result)


async def collect_user_info(function_name, tool_call_id, args, llm, context, result_callback):
    """
    Function 2: Collect user information for scheme application
    Returns Hindi text confirming collected information
    """
    logger.info(f"📝 Collecting user info with args: {args}")
    
    name = args.get("name", "")
    age = args.get("age", 0)
    state = args.get("state", "")
    education = args.get("education_level", "")
    
    # Create confirmation message in Hindi
    response_text = f"धन्यवाद! मैंने आपकी जानकारी सहेज ली है। "
    response_text += f"आपका नाम {name} है, आपकी उम्र {age} वर्ष है, "
    response_text += f"आप {state} राज्य से हैं और आपकी शिक्षा का स्तर {education} है। "
    response_text += "अब मैं आपके लिए उपयुक्त योजनाएं ढूंढ सकती हूं। क्या आप अपनी वार्षिक आय बताना चाहेंगे?"
    
    result = {
        "success": True,
        "collected_info": {
            "name": name,
            "age": age,
            "state": state,
            "education_level": education
        },
        "message": response_text,
        "next_step": "income_inquiry"
    }
    
    await result_callback(result)


async def get_scheme_details(function_name, tool_call_id, args, llm, context, result_callback):
    """
    Function 3: Get detailed information about a specific scheme
    Returns Hindi text with scheme details
    """
    logger.info(f"📋 Getting scheme details with args: {args}")
    
    scheme_name = args.get("scheme_name", "")
    detail_type = args.get("detail_type", "general")
    
    # Dummy scheme database
    scheme_database = {
        "प्री-मैट्रिक स्कॉलरशिप योजना": {
            "general": "यह योजना कक्षा एक से दस तक के छात्रों के लिए है। इसमें ट्यूशन फीस, किताबें और यूनिफॉर्म के लिए सहायता मिलती है।",
            "eligibility": "पारिवारिक आय ढाई लाख रुपये से कम होनी चाहिए। छात्र किसी मान्यता प्राप्त स्कूल में पढ़ रहा हो।",
            "documents": "आधार कार्ड, आय प्रमाण पत्र, जाति प्रमाण पत्र, स्कूल का आईडी कार्ड, बैंक पासबुक की कॉपी चाहिए।",
            "amount": "इस योजना में पांच हजार से पंद्रह हजार रुपये तक की वार्षिक सहायता मिलती है।"
        },
        "पोस्ट-मैट्रिक स्कॉलरशिप योजना": {
            "general": "यह योजना दसवीं कक्षा के बाद की पढ़ाई के लिए है। कॉलेज और विश्वविद्यालय के छात्र इसके लिए आवेदन कर सकते हैं।",
            "eligibility": "पारिवारिक आय पांच लाख रुपये से कम होनी चाहिए। पिछली परीक्षा में कम से कम पचास प्रतिशत अंक होने चाहिए।",
            "documents": "आधार कार्ड, आय प्रमाण पत्र, दसवीं और बारहवीं की मार्कशीट, कॉलेज का प्रवेश पत्र, बैंक विवरण।",
            "amount": "इस योजना में बीस हजार से पचास हजार रुपये तक की वार्षिक छात्रवृत्ति मिलती है।"
        },
        "एस सी एस टी छात्रवृत्ति योजना": {
            "general": "यह योजना विशेष रूप से अनुसूचित जाति और अनुसूचित जनजाति के छात्रों के लिए है। इसमें शिक्षा की सभी लागतें शामिल हैं।",
            "eligibility": "छात्र अनुसूचित जाति या जनजाति से होना चाहिए। नियमित रूप से कक्षाओं में उपस्थित रहना आवश्यक है।",
            "documents": "जाति प्रमाण पत्र, आधार कार्ड, आय प्रमाण पत्र, शैक्षिक प्रमाण पत्र, बैंक खाता विवरण।",
            "amount": "इस योजना में तीस हजार से अस्सी हजार रुपये तक की सहायता मिल सकती है।"
        },
        "मेरिट कम मीन्स स्कॉलरशिप": {
            "general": "यह योजना प्रतिभाशाली किंतु आर्थिक रूप से कमजोर छात्रों के लिए है। स्नातक और परास्नातक छात्र आवेदन कर सकते हैं।",
            "eligibility": "पिछली परीक्षा में साठ प्रतिशत से अधिक अंक होने चाहिए। पारिवारिक आय छह लाख रुपये से कम होनी चाहिए।",
            "documents": "अंकतालिका, आय प्रमाण पत्र, आधार कार्ड, बैंक खाता विवरण, कॉलेज का बोनाफाइड।",
            "amount": "इस योजना में बारह हजार से पचास हजार रुपये तक की छात्रवृत्ति मिलती है।"
        }
    }
    
    # Get scheme details
    if scheme_name in scheme_database:
        scheme_info = scheme_database[scheme_name]
        if detail_type in scheme_info:
            response_text = f"{scheme_name} के बारे में जानकारी: {scheme_info[detail_type]}"
        else:
            response_text = f"{scheme_name} के बारे में सामान्य जानकारी: {scheme_info['general']}"
    else:
        response_text = f"माफ़ कीजिये, {scheme_name} के बारे में मेरे पास जानकारी उपलब्ध नहीं है। कृपया किसी अन्य योजना के बारे में पूछें।"
    
    result = {
        "scheme_name": scheme_name,
        "detail_type": detail_type,
        "message": response_text,
        "found": scheme_name in scheme_database
    }
    
    await result_callback(result)
