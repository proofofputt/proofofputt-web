"""
Comprehensive test suite for database operations and API functions.
Tests all critical functionality to ensure system reliability.
"""

import os
import sys
import traceback
from datetime import datetime
import json

# Add the current directory to sys.path for imports
sys.path.append(os.path.dirname(__file__))

# Set up database connection
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_QFzNhl5WO4AE@ep-raspy-firefly-adagp7cf-pooler.c-2.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'

try:
    import data_manager
    from calibration import save_calibration_to_database, load_calibration_from_database, infer_hole_quadrants
    from session_reporter import SessionReporter
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

def test_database_connection():
    """Test basic database connectivity."""
    print("\n=== Testing Database Connection ===")
    try:
        pool = data_manager.get_db_connection()
        with pool.connect() as conn:
            result = conn.execute(data_manager.sqlalchemy.text('SELECT 1 as test')).mappings().first()
            assert result['test'] == 1
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_player_stats():
    """Test player stats calculation and safety functions."""
    print("\n=== Testing Player Stats ===")
    try:
        # Test safe_divide function
        assert data_manager.safe_divide(10, 2) == 5.0
        assert data_manager.safe_divide(10, 0) == 0
        assert data_manager.safe_divide(10, None) == 0
        print("✅ Safe divide function works correctly")
        
        # Test safe_value function
        assert data_manager.safe_value(10) == 10
        assert data_manager.safe_value(None) == 0
        assert data_manager.safe_value(float('inf')) == 0
        print("✅ Safe value function works correctly")
        
        # Test get_player_stats for default user
        stats = data_manager.get_player_stats(1)
        if stats:
            print(f"✅ Retrieved stats for player 1: {stats['sum_makes']} makes")
            
            # Verify no None or inf values in critical stats
            critical_fields = ['sum_makes', 'avg_accuracy', 'avg_ppm', 'low_fastest_21']
            for field in critical_fields:
                value = stats.get(field, 0)
                assert value is not None and value != float('inf')
                print(f"  - {field}: {value}")
            
            return True
        else:
            print("❌ No stats found for player 1")
            return False
            
    except Exception as e:
        print(f"❌ Player stats test failed: {e}")
        traceback.print_exc()
        return False

def test_recalculate_stats():
    """Test stats recalculation functionality."""
    print("\n=== Testing Stats Recalculation ===")
    try:
        result = data_manager.recalculate_player_stats(1)
        print(f"✅ Stats recalculated for player 1: {result}")
        return True
    except Exception as e:
        print(f"❌ Stats recalculation failed: {e}")
        traceback.print_exc()
        return False

def test_calibration_functions():
    """Test calibration save/load functionality."""
    print("\n=== Testing Calibration Functions ===")
    try:
        # Create test calibration data
        test_calibration = {
            "HOLE_ROI": [[100, 100], [150, 100], [150, 150], [100, 150]],
            "CATCH_ROI": [[200, 200], [250, 200], [250, 250], [200, 250]],
            "RETURN_ROI": [[50, 200], [100, 200], [100, 250], [50, 250]],
            "MAT_ROI": [[0, 300], [300, 300], [300, 400], [0, 400]],
            "camera_index": 0
        }
        
        # Test ROI inference
        test_roi_data = test_calibration.copy()
        success = infer_hole_quadrants(test_roi_data)
        if success:
            print("✅ ROI quadrant inference successful")
            print(f"  - Generated {len([k for k in test_roi_data.keys() if 'HOLE_' in k and 'ROI' in k])} quadrant ROIs")
        else:
            print("❌ ROI quadrant inference failed")
            return False
        
        # Test save calibration
        save_success = save_calibration_to_database(1, test_calibration)
        if save_success:
            print("✅ Calibration data saved successfully")
        else:
            print("❌ Failed to save calibration data")
            return False
        
        # Test load calibration
        loaded_calibration = load_calibration_from_database(1)
        if loaded_calibration:
            print("✅ Calibration data loaded successfully")
            # Verify key fields exist
            for key in ["HOLE_ROI", "CATCH_ROI", "calibration_timestamp"]:
                assert key in loaded_calibration
            print(f"  - Contains {len(loaded_calibration)} configuration items")
        else:
            print("❌ Failed to load calibration data")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Calibration test failed: {e}")
        traceback.print_exc()
        return False

def test_session_reporter():
    """Test session reporting functionality."""
    print("\n=== Testing Session Reporter ===")
    try:
        # Create sample putt data
        sample_putts = [
            {
                'current_frame_time': '10.0',
                'classification': 'MAKE',
                'detailed_classification': 'MAKE - TOP'
            },
            {
                'current_frame_time': '15.5',
                'classification': 'MISS',
                'detailed_classification': 'MISS - CATCH'
            },
            {
                'current_frame_time': '22.3',
                'classification': 'MAKE',
                'detailed_classification': 'MAKE - RIGHT'
            }
        ]
        
        # Create reporter instance
        reporter = SessionReporter(sample_putts)
        reporter.process_data()
        
        # Verify calculations
        assert reporter.total_putts == 3
        assert reporter.total_makes == 2
        assert reporter.total_misses == 1
        
        print("✅ Session reporter basic calculations correct")
        print(f"  - Total putts: {reporter.total_putts}")
        print(f"  - Makes: {reporter.total_makes}, Misses: {reporter.total_misses}")
        print(f"  - Make percentage: {reporter.make_percentage:.1f}%")
        
        # Test fastest 21 handling (should be inf with only 3 putts)
        assert reporter.fastest_21_makes == float('inf')
        print("✅ Fastest 21 calculation handles insufficient data correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Session reporter test failed: {e}")
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test various edge cases and error conditions."""
    print("\n=== Testing Edge Cases ===")
    try:
        # Test with non-existent player
        stats = data_manager.get_player_stats(999999)
        assert stats is None
        print("✅ Handles non-existent player correctly")
        
        # Test calibration with invalid data
        save_result = save_calibration_to_database(None, None)
        assert save_result == False
        print("✅ Handles invalid calibration data correctly")
        
        # Test calibration load with non-existent player
        cal_data = load_calibration_from_database(999999)
        assert cal_data is None
        print("✅ Handles non-existent calibration correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Edge case test failed: {e}")
        traceback.print_exc()
        return False

def run_full_test_suite():
    """Run the complete test suite."""
    print("🔬 Starting Proof of Putt Test Suite")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)
    
    if not IMPORTS_AVAILABLE:
        print("❌ Critical imports failed - cannot run tests")
        return False
    
    # List of all test functions
    tests = [
        test_database_connection,
        test_player_stats,
        test_recalculate_stats,
        test_calibration_functions,
        test_session_reporter,
        test_edge_cases
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    # Run each test
    for test_func in tests:
        try:
            result = test_func()
            if result:
                passed_tests += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! System is healthy.")
    else:
        print("⚠️  Some tests failed. Review errors above.")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = run_full_test_suite()
    sys.exit(0 if success else 1)