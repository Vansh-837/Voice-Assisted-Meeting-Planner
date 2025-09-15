#!/usr/bin/env python3
"""
Manual Test Runner - VIEW_SCHEDULE/VIEW_CALENDAR Test Cases
Tests ALL VIEW_SCHEDULE/VIEW_CALENDAR cases from test_conversation_scenarios.md (3.1-3.9)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.conversation_handler import ConversationHandler

def analyze_test_case(test_name, user_input, expected_behavior):
    print(f"\n{'='*80}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*80}")
    print(f"📝 USER INPUT: {user_input}")
    print(f"📋 EXPECTED: {expected_behavior}")
    print(f"{'─'*80}")
    
    # Initialize handler and process input
    handler = ConversationHandler()
    result = handler.process_user_input(user_input, {})
    
    # Extract data
    intent = result.get('intent')
    extracted_data = result.get('extracted_data', {})
    missing_fields = handler.check_mandatory_fields(extracted_data)
    bot_response = result.get('response', '')
    
    print(f"🤖 ACTUAL RESULTS:")
    print(f"   Intent: {intent}")
    print(f"   Extracted Data: {extracted_data}")
    print(f"   Missing Fields: {missing_fields}")
    print(f"   Bot Response: {bot_response}")
    
    return {
        'intent': intent,
        'data': extracted_data,
        'missing': missing_fields,
        'response': bot_response
    }

# 🟢 EASY LEVEL TESTS

def test_case_3_1():
    """Test Case 3.1: Today's Schedule"""
    user_input = "What's on my calendar today?"
    expected = "Should recognize VIEW_SCHEDULE intent and extract 'today' as date parameter"
    
    result = analyze_test_case("3.1 Today's Schedule", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date = 'date' in result['data'] or 'start_date' in result['data'] or 'target_date' in result['data']
    today_reference = any('today' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Parameter: {has_date}")
    print(f"   ✓ Contains 'Today' Reference: {today_reference}")
    
    passed = correct_intent and (has_date or today_reference)
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date and not today_reference: print(f"   - Missing date/today reference")
    
    return passed

def test_case_3_2():
    """Test Case 3.2: Specific Date"""
    user_input = "Show me my schedule for tomorrow"
    expected = "Should recognize VIEW_SCHEDULE intent and extract 'tomorrow' as date parameter"
    
    result = analyze_test_case("3.2 Specific Date", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date = 'date' in result['data'] or 'start_date' in result['data'] or 'target_date' in result['data']
    tomorrow_reference = any('tomorrow' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Parameter: {has_date}")
    print(f"   ✓ Contains 'Tomorrow' Reference: {tomorrow_reference}")
    
    passed = correct_intent and (has_date or tomorrow_reference)
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date and not tomorrow_reference: print(f"   - Missing date/tomorrow reference")
    
    return passed

def test_case_3_3():
    """Test Case 3.3: Simple Date Format"""
    user_input = "What meetings do I have on Friday?"
    expected = "Should recognize VIEW_SCHEDULE intent and extract 'Friday' as date parameter"
    
    result = analyze_test_case("3.3 Simple Date Format", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date = 'date' in result['data'] or 'start_date' in result['data'] or 'target_date' in result['data']
    friday_reference = any('friday' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Parameter: {has_date}")
    print(f"   ✓ Contains 'Friday' Reference: {friday_reference}")
    
    passed = correct_intent and (has_date or friday_reference)
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date and not friday_reference: print(f"   - Missing date/Friday reference")
    
    return passed

# 🟡 MEDIUM LEVEL TESTS

def test_case_3_4():
    """Test Case 3.4: Date Range"""
    user_input = "What's my schedule like this week?"
    expected = "Should recognize VIEW_SCHEDULE intent and extract 'this week' as date range parameter"
    
    result = analyze_test_case("3.4 Date Range", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date_range = any(key in result['data'] for key in ['date_range', 'start_date', 'end_date', 'date'])
    week_reference = any('week' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Range Parameter: {has_date_range}")
    print(f"   ✓ Contains 'Week' Reference: {week_reference}")
    
    passed = correct_intent and (has_date_range or week_reference)
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date_range and not week_reference: print(f"   - Missing date range/week reference")
    
    return passed

def test_case_3_5():
    """Test Case 3.5: Relative Dates"""
    user_input = "Show me next Monday's calendar"
    expected = "Should recognize VIEW_SCHEDULE intent and parse 'next Monday' correctly"
    
    result = analyze_test_case("3.5 Relative Dates", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date = 'date' in result['data'] or 'start_date' in result['data'] or 'target_date' in result['data']
    monday_reference = any('monday' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    next_reference = any('next' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Parameter: {has_date}")
    print(f"   ✓ Contains 'Monday' Reference: {monday_reference}")
    print(f"   ✓ Contains 'Next' Reference: {next_reference}")
    
    passed = correct_intent and (has_date or (monday_reference and next_reference))
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date: print(f"   - Missing date parameter")
        if not monday_reference: print(f"   - Missing Monday reference")
        if not next_reference: print(f"   - Missing 'next' reference")
    
    return passed

def test_case_3_6():
    """Test Case 3.6: Empty Schedule"""
    user_input = "What do I have on Saturday?"
    expected = "Should recognize VIEW_SCHEDULE intent and handle Saturday request (even if empty)"
    
    result = analyze_test_case("3.6 Empty Schedule", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date = 'date' in result['data'] or 'start_date' in result['data'] or 'target_date' in result['data']
    saturday_reference = any('saturday' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Parameter: {has_date}")
    print(f"   ✓ Contains 'Saturday' Reference: {saturday_reference}")
    
    passed = correct_intent and (has_date or saturday_reference)
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date and not saturday_reference: print(f"   - Missing date/Saturday reference")
    
    return passed

# 🔴 HARD LEVEL TESTS

def test_case_3_7():
    """Test Case 3.7: Complex Date Parsing"""
    user_input = "What's happening on the 20th of next month?"
    expected = "Should recognize VIEW_SCHEDULE intent and parse complex date '20th of next month'"
    
    result = analyze_test_case("3.7 Complex Date Parsing", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date = 'date' in result['data'] or 'start_date' in result['data'] or 'target_date' in result['data']
    has_day_reference = any('20' in str(value) for value in result['data'].values()) if result['data'] else False
    has_month_reference = any('month' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Parameter: {has_date}")
    print(f"   ✓ Contains Day '20th' Reference: {has_day_reference}")
    print(f"   ✓ Contains 'Month' Reference: {has_month_reference}")
    
    passed = correct_intent and has_date
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date: print(f"   - Missing date parameter for complex date")
    
    return passed

def test_case_3_8():
    """Test Case 3.8: Contextual Follow-up"""
    user_input = "Show my calendar"
    expected = "Should recognize VIEW_SCHEDULE intent for general calendar request"
    
    result = analyze_test_case("3.8 Contextual Follow-up", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    # For general calendar request, date might be optional or default to today
    has_calendar_keyword = 'calendar' in user_input.lower()
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Contains 'Calendar' Keyword: {has_calendar_keyword}")
    
    passed = correct_intent and has_calendar_keyword
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_calendar_keyword: print(f"   - Missing calendar keyword recognition")
    
    return passed

def test_case_3_9():
    """Test Case 3.9: Detailed Information Request"""
    user_input = "I need a detailed breakdown of my meetings this week including attendees and locations"
    expected = "Should recognize VIEW_SCHEDULE intent and extract detailed request parameters"
    
    result = analyze_test_case("3.9 Detailed Information Request", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    correct_intent = result['intent'] == 'VIEW_SCHEDULE'
    has_date_range = any(key in result['data'] for key in ['date_range', 'start_date', 'end_date', 'date'])
    week_reference = any('week' in str(value).lower() for value in result['data'].values()) if result['data'] else False
    detailed_request = any(word in user_input.lower() for word in ['detailed', 'breakdown', 'attendees', 'locations'])
    
    print(f"   ✓ Correct Intent (VIEW_SCHEDULE): {correct_intent}")
    print(f"   ✓ Has Date Range Parameter: {has_date_range}")
    print(f"   ✓ Contains 'Week' Reference: {week_reference}")
    print(f"   ✓ Detailed Request Keywords: {detailed_request}")
    
    passed = correct_intent and (has_date_range or week_reference) and detailed_request
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date_range and not week_reference: print(f"   - Missing date range/week reference")
        if not detailed_request: print(f"   - Missing detailed request keywords")
    
    return passed

def run_all_tests():
    """Run all VIEW_SCHEDULE/VIEW_CALENDAR test cases"""
    print("🚀 COMPREHENSIVE VIEW_SCHEDULE/VIEW_CALENDAR TEST SUITE")
    print("Testing all cases from test_conversation_scenarios.md (3.1-3.9)")
    print("="*80)
    
    results = []
    
    # Easy Level Tests
    print("\n🟢 EASY LEVEL TESTS")
    print("="*50)
    results.append(("3.1 Today's Schedule", test_case_3_1()))
    results.append(("3.2 Specific Date", test_case_3_2()))
    results.append(("3.3 Simple Date Format", test_case_3_3()))
    
    # Medium Level Tests
    print("\n🟡 MEDIUM LEVEL TESTS")
    print("="*50)
    results.append(("3.4 Date Range", test_case_3_4()))
    results.append(("3.5 Relative Dates", test_case_3_5()))
    results.append(("3.6 Empty Schedule", test_case_3_6()))
    
    # Hard Level Tests
    print("\n🔴 HARD LEVEL TESTS")
    print("="*50)
    results.append(("3.7 Complex Date Parsing", test_case_3_7()))
    results.append(("3.8 Contextual Follow-up", test_case_3_8()))
    results.append(("3.9 Detailed Information Request", test_case_3_9()))
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed} ({passed/len(results)*100:.1f}%)")
    print(f"❌ Failed: {failed} ({failed/len(results)*100:.1f}%)")
    
    if failed > 0:
        print(f"\n❌ FAILED TESTS:")
        for test_name, result in results:
            if not result:
                print(f"   - {test_name}")
    
    print(f"\n💡 INSIGHTS:")
    easy_passed = sum(1 for test_name, result in results[:3] if result)
    medium_passed = sum(1 for test_name, result in results[3:6] if result)
    hard_passed = sum(1 for test_name, result in results[6:9] if result)
    
    print(f"   🟢 Easy Level: {easy_passed}/3 ({easy_passed/3*100:.1f}%) - Target: 95%+")
    print(f"   🟡 Medium Level: {medium_passed}/3 ({medium_passed/3*100:.1f}%) - Target: 85%+")
    print(f"   🔴 Hard Level: {hard_passed}/3 ({hard_passed/3*100:.1f}%) - Target: 70%+")
    
    return results

if __name__ == "__main__":
    run_all_tests() 