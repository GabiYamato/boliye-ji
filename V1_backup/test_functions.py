"""
Standalone test script for Hindi Voice Agent
This script helps you test the bot logic without full Twilio/BentoML setup
"""

import asyncio
import json
from scheme_functions import check_eligibility, collect_user_info, get_scheme_details


async def test_callback(result):
    """Callback function to receive results from functions"""
    print("\n" + "="*60)
    print("📥 FUNCTION RESULT:")
    print("="*60)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("="*60 + "\n")


async def test_eligibility_function():
    """Test the eligibility checking function"""
    print("\n🔍 Testing Eligibility Check Function")
    print("-" * 60)
    
    # Test case 1: SC category, low income
    print("\n📋 Test Case 1: SC category, income 200,000")
    args = {
        "category": "अनुसूचित जाति",
        "annual_income": 200000,
        "education_level": "उच्च माध्यमिक"
    }
    await check_eligibility(
        "check_eligibility", 
        "test_call_1", 
        args, 
        None, 
        None, 
        test_callback
    )
    
    # Test case 2: General category, medium income
    print("\n📋 Test Case 2: General category, income 450,000")
    args = {
        "category": "सामान्य",
        "annual_income": 450000,
        "education_level": "स्नातक"
    }
    await check_eligibility(
        "check_eligibility", 
        "test_call_2", 
        args, 
        None, 
        None, 
        test_callback
    )
    
    # Test case 3: High income (no eligibility)
    print("\n📋 Test Case 3: High income 700,000")
    args = {
        "category": "सामान्य",
        "annual_income": 700000,
        "education_level": "माध्यमिक"
    }
    await check_eligibility(
        "check_eligibility", 
        "test_call_3", 
        args, 
        None, 
        None, 
        test_callback
    )


async def test_info_collection_function():
    """Test the information collection function"""
    print("\n📝 Testing Info Collection Function")
    print("-" * 60)
    
    # Test case: Collect student information
    print("\n📋 Test Case: Student from Bihar")
    args = {
        "name": "राज कुमार",
        "age": 17,
        "state": "बिहार",
        "education_level": "उच्च माध्यमिक"
    }
    await collect_user_info(
        "collect_user_info", 
        "test_call_4", 
        args, 
        None, 
        None, 
        test_callback
    )


async def test_scheme_details_function():
    """Test the scheme details function"""
    print("\n📋 Testing Scheme Details Function")
    print("-" * 60)
    
    # Test case 1: Pre-matric scheme - general info
    print("\n📋 Test Case 1: Pre-matric scheme - General Info")
    args = {
        "scheme_name": "प्री-मैट्रिक स्कॉलरशिप योजना",
        "detail_type": "general"
    }
    await get_scheme_details(
        "get_scheme_details", 
        "test_call_5", 
        args, 
        None, 
        None, 
        test_callback
    )
    
    # Test case 2: Post-matric scheme - eligibility
    print("\n📋 Test Case 2: Post-matric scheme - Eligibility")
    args = {
        "scheme_name": "पोस्ट-मैट्रिक स्कॉलरशिप योजना",
        "detail_type": "eligibility"
    }
    await get_scheme_details(
        "get_scheme_details", 
        "test_call_6", 
        args, 
        None, 
        None, 
        test_callback
    )
    
    # Test case 3: SC/ST scheme - documents
    print("\n📋 Test Case 3: SC/ST scheme - Documents")
    args = {
        "scheme_name": "एस सी एस टी छात्रवृत्ति योजना",
        "detail_type": "documents"
    }
    await get_scheme_details(
        "get_scheme_details", 
        "test_call_7", 
        args, 
        None, 
        None, 
        test_callback
    )
    
    # Test case 4: Merit scheme - amount
    print("\n📋 Test Case 4: Merit scheme - Amount Info")
    args = {
        "scheme_name": "मेरिट कम मीन्स स्कॉलरशिप",
        "detail_type": "amount"
    }
    await get_scheme_details(
        "get_scheme_details", 
        "test_call_8", 
        args, 
        None, 
        None, 
        test_callback
    )
    
    # Test case 5: Unknown scheme
    print("\n📋 Test Case 5: Unknown Scheme")
    args = {
        "scheme_name": "अज्ञात योजना",
        "detail_type": "general"
    }
    await get_scheme_details(
        "get_scheme_details", 
        "test_call_9", 
        args, 
        None, 
        None, 
        test_callback
    )


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 HINDI VOICE AGENT - FUNCTION TESTING")
    print("="*60)
    print("This script tests the 3 function calling capabilities:")
    print("  1. check_eligibility - Check scheme eligibility")
    print("  2. collect_user_info - Collect student information")
    print("  3. get_scheme_details - Get scheme details")
    print("="*60)
    
    # Run all tests
    await test_eligibility_function()
    await test_info_collection_function()
    await test_scheme_details_function()
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)
    print("\n💡 Next Steps:")
    print("  1. Review the Hindi responses above")
    print("  2. Make sure the text is clear and natural")
    print("  3. Test with actual TTS to hear the audio quality")
    print("  4. Deploy the full service with hindi_voice_service.py")
    print("="*60 + "\n")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())
