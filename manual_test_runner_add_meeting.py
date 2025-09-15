#!/usr/bin/env python3
"""
Manual Test Runner - Actually runs each test case and analyzes real behavior
Tests ALL ADD_MEETING cases from test_conversation_scenarios.md (except 1.9)
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

def test_case_1_1():
    """Test Case 1.1: Complete Information"""
    user_input = "Schedule a project review meeting with shreysoni009@gmail.com tomorrow at 2 PM for 1 hour"
    expected = "Should extract all fields (title, time, duration, attendees) with no missing fields"
    
    result = analyze_test_case("1.1 Complete Information", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    has_title = bool(result['data'].get('meeting_title'))
    has_time = bool(result['data'].get('start_datetime'))
    has_duration = bool(result['data'].get('duration_minutes'))
    has_attendees = bool(result['data'].get('attendees'))
    no_missing = len(result['missing']) == 0
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Has Title: {has_title}")
    print(f"   ✓ Has Time: {has_time}")
    print(f"   ✓ Has Duration: {has_duration}")
    print(f"   ✓ Has Attendees: {has_attendees}")
    print(f"   ✓ No Missing Fields: {no_missing}")
    
    passed = all([correct_intent, has_title, has_time, has_duration, has_attendees, no_missing])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_title: print(f"   - Missing title")
        if not has_time: print(f"   - Missing time")
        if not has_duration: print(f"   - Missing duration")
        if not has_attendees: print(f"   - Missing attendees")
        if not no_missing: print(f"   - Has missing fields: {result['missing']}")
    
    return passed

def test_case_1_2():
    """Test Case 1.2: Basic Meeting"""
    user_input = "Book a team standup meeting for today at 9 AM with shreysoni009@gmail.com"
    expected = "Should extract title, time, attendees. Duration can be missing (default acceptable)"
    
    result = analyze_test_case("1.2 Basic Meeting", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    has_title = bool(result['data'].get('meeting_title'))
    has_time = bool(result['data'].get('start_datetime'))
    has_attendees = bool(result['data'].get('attendees'))
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Has Title: {has_title}")
    print(f"   ✓ Has Time: {has_time}")
    print(f"   ✓ Has Attendees: {has_attendees}")
    
    passed = all([correct_intent, has_title, has_time, has_attendees])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_title: print(f"   - Missing title")
        if not has_time: print(f"   - Missing time")
        if not has_attendees: print(f"   - Missing attendees")
    
    return passed

def test_case_1_3():
    """Test Case 1.3: Simple Time Format"""
    user_input = "Add a lunch meeting with shreysoni009@gmail.com at 12:30 PM tomorrow"
    expected = "Should parse 12:30 PM time correctly and extract attendee"
    
    result = analyze_test_case("1.3 Simple Time Format", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    has_time = 'start_datetime' in result['data'] and '12:30' in str(result['data'].get('start_datetime', ''))
    has_attendees = 'attendees' in result['data'] and 'shreysoni009@gmail.com' in str(result['data'].get('attendees', []))
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Time Parsed (12:30): {has_time}")
    print(f"   ✓ Attendees Extracted: {has_attendees}")
    
    passed = all([correct_intent, has_time, has_attendees])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_time: print(f"   - Didn't parse 12:30 PM correctly")
        if not has_attendees: print(f"   - Didn't extract shreysoni009@gmail.com")
    
    return passed

# 🟡 MEDIUM LEVEL TESTS

def test_case_1_4():
    """Test Case 1.4: Missing Duration and Title"""
    user_input = "I need to schedule a meeting with the marketing team tomorrow at 3 PM"
    expected = "Should extract time and team reference, but ask for title, duration, and specific attendee emails"
    
    result = analyze_test_case("1.4 Missing Duration and Title", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    has_time = 'start_datetime' in result['data'] and '15:00' in str(result['data'].get('start_datetime', ''))
    has_team_ref = 'attendees' in result['data'] and any('team' in str(att).lower() for att in result['data'].get('attendees', []))
    missing_title = 'meeting_title' in result['missing']
    missing_duration = 'duration_minutes' in result['missing'] 
    missing_attendees = 'attendees' in result['missing']  # Should be missing due to team reference
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Extracted Time (3 PM): {has_time}")
    print(f"   ✓ Extracted Team Reference: {has_team_ref}")
    print(f"   ✓ Missing Title (should ask): {missing_title}")
    print(f"   ✓ Missing Duration (should ask): {missing_duration}")
    print(f"   ✓ Missing Attendees (team ref, should ask for emails): {missing_attendees}")
    
    passed = all([correct_intent, has_time, has_team_ref, missing_title, missing_duration, missing_attendees])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_time: print(f"   - Didn't extract 3 PM time correctly")
        if not has_team_ref: print(f"   - Didn't extract 'marketing team' reference")
        if not missing_title: print(f"   - Should be missing title but isn't")
        if not missing_duration: print(f"   - Should be missing duration but isn't")
        if not missing_attendees: print(f"   - Should be missing attendees (team ref) but isn't")
    
    return passed

def test_case_1_5():
    """Test Case 1.5: Missing Title and Time"""
    user_input = "Can you set up a meeting with shreysoni009@gmail.com and kushal.multiqos@gmail.com next Tuesday?"
    expected = "Should extract attendees but be missing title, time, and duration"
    
    result = analyze_test_case("1.5 Missing Title and Time", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    has_attendees = 'attendees' in result['data'] and len(result['data'].get('attendees', [])) >= 2
    missing_title = 'meeting_title' in result['missing']
    missing_time = 'start_datetime' in result['missing']
    missing_duration = 'duration_minutes' in result['missing']
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Has Attendees (2+): {has_attendees}")
    print(f"   ✓ Missing Title (should ask): {missing_title}")
    print(f"   ✓ Missing Time (should ask): {missing_time}")
    print(f"   ✓ Missing Duration (should ask): {missing_duration}")
    
    passed = all([correct_intent, has_attendees, missing_title, missing_time, missing_duration])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_attendees: print(f"   - Should extract 2+ attendees")
        if not missing_title: print(f"   - Should be missing title")
        if not missing_time: print(f"   - Should be missing time")
        if not missing_duration: print(f"   - Should be missing duration")
    
    return passed

def test_case_1_6():
    """Test Case 1.6: Conflict Resolution with Title"""
    user_input = "Schedule a client call meeting with shreysoni009@gmail.com tomorrow at 12:30 PM"
    expected = "Should extract title, time, and attendees"
    
    result = analyze_test_case("1.6 Conflict Resolution", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    has_title = 'meeting_title' in result['data'] and 'client call' in str(result['data'].get('meeting_title', '')).lower()
    has_time = 'start_datetime' in result['data'] and '12:30' in str(result['data'].get('start_datetime', ''))
    has_attendees = 'attendees' in result['data'] and 'shreysoni009@gmail.com' in str(result['data'].get('attendees', []))
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Has Title (client call): {has_title}")
    print(f"   ✓ Has Time (12:30 PM): {has_time}")
    print(f"   ✓ Has Attendees: {has_attendees}")
    
    passed = all([correct_intent, has_title, has_time, has_attendees])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_title: print(f"   - Should extract 'client call' title")
        if not has_time: print(f"   - Should extract 12:30 PM time")
        if not has_attendees: print(f"   - Should extract attendee")
    
    return passed

# 🔴 HARD LEVEL TESTS

def test_case_1_7():
    """Test Case 1.7: Complex Time Zones with Missing Title"""
    user_input = "I need to meet with the London team next Friday"
    expected = "Should extract date but ask for title, time, duration, and specific attendee emails"
    
    result = analyze_test_case("1.7 Complex Time Zones", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    has_date = 'start_datetime' in result['data']
    has_team_ref = 'attendees' in result['data'] and any('team' in str(att).lower() for att in result['data'].get('attendees', []))
    missing_title = 'meeting_title' in result['missing']
    missing_time = 'start_datetime' in result['missing']  # Should be missing due to midnight
    missing_duration = 'duration_minutes' in result['missing']
    missing_attendees = 'attendees' in result['missing']  # Should be missing due to team reference
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Extracted Date Reference: {has_date}")
    print(f"   ✓ Extracted Team Reference: {has_team_ref}")
    print(f"   ✓ Missing Title (should ask): {missing_title}")
    print(f"   ✓ Missing Time (should ask for specific time): {missing_time}")
    print(f"   ✓ Missing Duration (should ask): {missing_duration}")
    print(f"   ✓ Missing Attendees (team ref, should ask for emails): {missing_attendees}")
    
    passed = all([correct_intent, has_date, has_team_ref, missing_title, missing_time, missing_duration, missing_attendees])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not has_date: print(f"   - Didn't extract Friday date reference")
        if not has_team_ref: print(f"   - Didn't extract 'London team' reference")
        if not missing_title: print(f"   - Should be missing title but isn't")
        if not missing_time: print(f"   - Should be missing time (midnight issue) but isn't")
        if not missing_duration: print(f"   - Should be missing duration but isn't")
        if not missing_attendees: print(f"   - Should be missing attendees (team ref) but isn't")
    
    return passed

def test_case_1_8():
    """Test Case 1.8: Ambiguous References"""
    user_input = "Set up that important meeting we discussed"
    expected = "Should be missing most fields due to vague reference"
    
    result = analyze_test_case("1.8 Ambiguous References", user_input, expected)
    
    # Analysis
    print(f"🔍 ANALYSIS:")
    missing_most = len(result['missing']) >= 3  # Should be missing most mandatory fields
    correct_intent = result['intent'] == 'ADD_MEETING'
    
    print(f"   ✓ Correct Intent (ADD_MEETING): {correct_intent}")
    print(f"   ✓ Missing Most Fields (3+): {missing_most}")
    print(f"   ✓ Missing Fields Count: {len(result['missing'])}")
    
    passed = all([correct_intent, missing_most])
    print(f"🎯 RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    if not passed:
        print(f"❗ ISSUES:")
        if not correct_intent: print(f"   - Wrong intent: {result['intent']}")
        if not missing_most: print(f"   - Should be missing 3+ fields due to vague input")
    
    return passed

def run_all_tests():
    """Run all ADD_MEETING test cases"""
    print("🚀 COMPREHENSIVE ADD_MEETING TEST SUITE")
    print("Testing all cases from test_conversation_scenarios.md (except 1.9)")
    print("="*80)
    
    results = []
    
    # Easy Level Tests
    print("\n🟢 EASY LEVEL TESTS")
    print("="*50)
    results.append(("1.1 Complete Information", test_case_1_1()))
    results.append(("1.2 Basic Meeting", test_case_1_2()))
    results.append(("1.3 Simple Time Format", test_case_1_3()))
    
    # Medium Level Tests
    print("\n🟡 MEDIUM LEVEL TESTS")
    print("="*50)
    results.append(("1.4 Missing Duration and Title", test_case_1_4()))
    results.append(("1.5 Missing Title and Time", test_case_1_5()))
    results.append(("1.6 Conflict Resolution", test_case_1_6()))
    
    # Hard Level Tests
    print("\n🔴 HARD LEVEL TESTS")
    print("="*50)
    results.append(("1.7 Complex Time Zones", test_case_1_7()))
    results.append(("1.8 Ambiguous References", test_case_1_8()))
    
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
    hard_passed = sum(1 for test_name, result in results[6:8] if result)
    
    print(f"   🟢 Easy Level: {easy_passed}/3 ({easy_passed/3*100:.1f}%) - Target: 95%+")
    print(f"   🟡 Medium Level: {medium_passed}/3 ({medium_passed/3*100:.1f}%) - Target: 85%+")
    print(f"   🔴 Hard Level: {hard_passed}/2 ({hard_passed/2*100:.1f}%) - Target: 70%+")
    
    return results

if __name__ == "__main__":
    run_all_tests() 