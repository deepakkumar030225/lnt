"""
Test script to verify the FastAPI backend is working correctly
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing /health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_meta():
    """Test metadata endpoint"""
    print("\nTesting /meta endpoint...")
    response = requests.get(f"{API_URL}/meta")
    print(f"  Status: {response.status_code}")
    data = response.json()
    print(f"  Features count: {len(data['features'])}")
    print(f"  Model count: {data['model_count']}")
    return response.status_code == 200

def test_single_prediction():
    """Test single prediction endpoint"""
    print("\nTesting /predict/single endpoint...")
    
    test_input = {
        "Ambient_temp_C": 30,
        "Relative_humidity_pct": 60,
        "Wind_speed_mps": 2.0,
        "Season": "summer",
        "Daytime_hours": 12,
        "No_of_moulds": 10,
        "Cement_type": "OPC",
        "Cement_content_kgm3": 380,
        "Water_cement_ratio": 0.40,
        "Flyash_percent": 0,
        "Target_grade_MPa": 40,
        "Curing_method": "steam",
        "Steam_temp_C": 60,
        "Steam_duration_hr": 6,
        "Curing_start_delay_hr": 2,
        "Chamber_humidity_pct": 80,
        "Cleaning_time_min": 20,
        "Reset_time_min": 15,
        "Equipment_downtime_min": 10,
        "Energy_cost_rate_INR_per_kWh": 10.0,
        "Early_strength_requirement_MPa": 20.0,
        "Initial_strength_12hr_MPa": 0.0,
        "Maturity_index": 0.0,
        "Automation_level": 1
    }
    
    response = requests.post(f"{API_URL}/predict/single", json=test_input)
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✓ Demould Time: {result['Demould_Time_hr']:.2f} hours")
        print(f"  ✓ Cycle Time: {result['Cycle_Time_hr']:.2f} hours")
        print(f"  ✓ Total Cost: ₹{result['Total_Cost_INR']:,.0f}")
        return True
    else:
        print(f"  ✗ Error: {response.text}")
        return False

def test_batch_prediction():
    """Test batch prediction endpoint"""
    print("\nTesting /predict/batch endpoint...")
    
    # Create 3 test scenarios
    inputs = []
    for cement in [350, 380, 400]:
        inputs.append({
            "Ambient_temp_C": 30,
            "Cement_type": "OPC",
            "Cement_content_kgm3": cement,
            "Water_cement_ratio": 0.40,
            "Curing_method": "steam",
            "Steam_temp_C": 60,
            "Steam_duration_hr": 6,
            "Season": "summer",
            "Relative_humidity_pct": 60,
            "Wind_speed_mps": 2.0,
            "Daytime_hours": 12,
            "No_of_moulds": 10,
            "Flyash_percent": 0,
            "Target_grade_MPa": 40,
            "Curing_start_delay_hr": 2,
            "Chamber_humidity_pct": 80,
            "Cleaning_time_min": 20,
            "Reset_time_min": 15,
            "Equipment_downtime_min": 10,
            "Energy_cost_rate_INR_per_kWh": 10.0,
            "Early_strength_requirement_MPa": 20.0,
            "Initial_strength_12hr_MPa": 0.0,
            "Maturity_index": 0.0,
            "Automation_level": 1
        })
    
    response = requests.post(f"{API_URL}/predict/batch", json={"inputs": inputs})
    print(f"  Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✓ Processed {result['count']} scenarios")
        print("\n  Results:")
        for i, res in enumerate(result['results']):
            print(f"    Scenario {i+1} (Cement: {res['input_params']['Cement_content_kgm3']} kg/m³)")
            print(f"      → Cycle Time: {res['Cycle_Time_hr']:.2f} h | Cost: ₹{res['Total_Cost_INR']:,.0f}")
        return True
    else:
        print(f"  ✗ Error: {response.text}")
        return False

def main():
    print("=" * 60)
    print("  PRECAST AI OPTIMIZER - API TEST SUITE")
    print("=" * 60)
    
    try:
        # Run all tests
        results = []
        results.append(("Health Check", test_health()))
        results.append(("Metadata", test_meta()))
        results.append(("Single Prediction", test_single_prediction()))
        results.append(("Batch Prediction", test_batch_prediction()))
        
        # Summary
        print("\n" + "=" * 60)
        print("  TEST SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for test_name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {test_name}: {status}")
            if not passed:
                all_passed = False
        
        print("=" * 60)
        
        if all_passed:
            print("\n🎉 All tests passed! Backend is working correctly.")
            print("\nYou can now start the Streamlit frontend:")
            print("  streamlit run app.py")
        else:
            print("\n⚠️  Some tests failed. Please check the backend logs.")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend API")
        print("\nMake sure the backend is running:")
        print("  cd backend")
        print("  python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
