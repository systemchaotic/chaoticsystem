#!/usr/bin/env python3
"""
Backend API Testing for Idle Game Content API
Tests all CRUD operations for ContentPack endpoints
"""

import requests
import json
import uuid
from typing import Dict, Any

# Use the frontend environment variable for backend URL
BACKEND_URL = "/api"  # From frontend/.env REACT_APP_BACKEND_URL

def test_health_endpoint():
    """Test the health endpoint"""
    print("🔍 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") is True:
                print("✅ Health endpoint working correctly")
                return True
            else:
                print("❌ Health endpoint returned ok: false")
                return False
        else:
            print(f"❌ Health endpoint failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def create_sample_content_pack() -> Dict[str, Any]:
    """Create a realistic sample content pack for testing"""
    pack_id = str(uuid.uuid4())
    
    return {
        "id": pack_id,
        "title": "Medieval Fantasy Realm",
        "theme": "medieval_fantasy",
        "summary": "A comprehensive medieval fantasy content pack with kingdoms, magic, and ancient mysteries",
        "author_email": "gamedev@example.com",
        "resources": [
            {
                "id": str(uuid.uuid4()),
                "key": "gold",
                "name": "Gold Coins",
                "description": "The primary currency of the realm",
                "base_rate": 1.0
            },
            {
                "id": str(uuid.uuid4()),
                "key": "mana",
                "name": "Magical Energy",
                "description": "Mystical energy used for spells and enchantments",
                "base_rate": 0.5
            }
        ],
        "upgrades": [
            {
                "id": str(uuid.uuid4()),
                "key": "mining_efficiency",
                "name": "Enhanced Mining",
                "description": "Improves gold mining efficiency by 25%",
                "cost": {"gold": 100.0},
                "effects": {"gold_rate_multiplier": 1.25}
            },
            {
                "id": str(uuid.uuid4()),
                "key": "mana_crystal",
                "name": "Mana Crystal",
                "description": "Increases mana generation rate",
                "cost": {"gold": 250.0, "mana": 50.0},
                "effects": {"mana_rate_multiplier": 1.5}
            }
        ],
        "areas": [
            {
                "id": str(uuid.uuid4()),
                "key": "castle_grounds",
                "name": "Castle Grounds",
                "description": "The fortified heart of your kingdom",
                "unlock_conditions": {"gold": 0}
            },
            {
                "id": str(uuid.uuid4()),
                "key": "enchanted_forest",
                "name": "Enchanted Forest",
                "description": "A mystical woodland filled with magical creatures",
                "unlock_conditions": {"gold": 500, "mana": 100}
            }
        ],
        "factions": [
            {
                "id": str(uuid.uuid4()),
                "key": "royal_guard",
                "name": "Royal Guard",
                "description": "Elite warriors sworn to protect the realm",
                "traits": {"combat_bonus": 1.2, "loyalty": "high"}
            },
            {
                "id": str(uuid.uuid4()),
                "key": "mages_guild",
                "name": "Mages Guild",
                "description": "Ancient order of magical practitioners",
                "traits": {"mana_bonus": 1.3, "research_speed": 1.1}
            }
        ]
    }

def test_create_content_pack():
    """Test creating a new content pack"""
    print("\n🔍 Testing Create Content Pack...")
    
    sample_pack = create_sample_content_pack()
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/packs",
            json=sample_pack,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            created_pack = response.json()
            print(f"✅ Content pack created successfully")
            print(f"Created pack ID: {created_pack.get('id')}")
            
            # Verify all fields are present and UUIDs are strings
            if (created_pack.get('id') and 
                isinstance(created_pack.get('id'), str) and
                created_pack.get('title') == sample_pack['title'] and
                len(created_pack.get('resources', [])) == len(sample_pack['resources'])):
                print("✅ All fields properly serialized with UUID strings")
                return created_pack
            else:
                print("❌ Response structure or UUID serialization issue")
                return None
        else:
            print(f"❌ Create failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Create content pack error: {e}")
        return None

def test_list_content_packs():
    """Test listing all content packs"""
    print("\n🔍 Testing List Content Packs...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/packs")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            packs = response.json()
            print(f"✅ Retrieved {len(packs)} content packs")
            
            # Verify structure
            if isinstance(packs, list):
                for pack in packs:
                    if not isinstance(pack.get('id'), str):
                        print("❌ Pack ID not serialized as string")
                        return False
                print("✅ All pack IDs properly serialized as strings")
                return packs
            else:
                print("❌ Response is not a list")
                return None
        else:
            print(f"❌ List failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ List content packs error: {e}")
        return None

def test_get_content_pack(pack_id: str):
    """Test getting a specific content pack"""
    print(f"\n🔍 Testing Get Content Pack (ID: {pack_id})...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/packs/{pack_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            pack = response.json()
            print(f"✅ Retrieved content pack: {pack.get('title')}")
            
            # Verify UUID serialization
            if isinstance(pack.get('id'), str) and pack.get('id') == pack_id:
                print("✅ Pack ID properly serialized as string")
                return pack
            else:
                print("❌ Pack ID serialization issue")
                return None
        elif response.status_code == 404:
            print("❌ Pack not found (404)")
            return None
        else:
            print(f"❌ Get failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Get content pack error: {e}")
        return None

def test_update_content_pack(pack_id: str):
    """Test updating a content pack"""
    print(f"\n🔍 Testing Update Content Pack (ID: {pack_id})...")
    
    # Create updated pack data
    updated_pack = create_sample_content_pack()
    updated_pack['id'] = pack_id
    updated_pack['title'] = "Updated Medieval Fantasy Realm"
    updated_pack['summary'] = "An updated and expanded medieval fantasy experience"
    
    # Add a new resource to test nested array updates
    updated_pack['resources'].append({
        "id": str(uuid.uuid4()),
        "key": "wood",
        "name": "Timber",
        "description": "Essential building material from the enchanted forest",
        "base_rate": 0.8
    })
    
    try:
        response = requests.put(
            f"{BACKEND_URL}/packs/{pack_id}",
            json=updated_pack,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            updated = response.json()
            print(f"✅ Content pack updated successfully")
            print(f"New title: {updated.get('title')}")
            print(f"Resources count: {len(updated.get('resources', []))}")
            
            # Verify updates
            if (updated.get('title') == updated_pack['title'] and
                len(updated.get('resources', [])) == len(updated_pack['resources'])):
                print("✅ Update successful with proper nested array handling")
                return updated
            else:
                print("❌ Update verification failed")
                return None
        elif response.status_code == 404:
            print("❌ Pack not found for update (404)")
            return None
        else:
            print(f"❌ Update failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Update content pack error: {e}")
        return None

def test_delete_content_pack(pack_id: str):
    """Test deleting a content pack"""
    print(f"\n🔍 Testing Delete Content Pack (ID: {pack_id})...")
    
    try:
        response = requests.delete(f"{BACKEND_URL}/packs/{pack_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Content pack deleted successfully")
            print(f"Response: {result}")
            
            if result.get('ok') is True:
                return True
            else:
                print("❌ Delete response format issue")
                return False
        elif response.status_code == 404:
            print("❌ Pack not found for deletion (404)")
            return False
        else:
            print(f"❌ Delete failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Delete content pack error: {e}")
        return False

def test_get_deleted_pack(pack_id: str):
    """Test that getting a deleted pack returns 404"""
    print(f"\n🔍 Testing Get Deleted Pack (should return 404)...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/packs/{pack_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ Deleted pack correctly returns 404")
            return True
        else:
            print(f"❌ Expected 404 but got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Get deleted pack error: {e}")
        return False

def check_cors_and_headers():
    """Check CORS and content-type headers"""
    print("\n🔍 Testing CORS and Headers...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        headers = response.headers
        
        print(f"Content-Type: {headers.get('content-type')}")
        print(f"Access-Control-Allow-Origin: {headers.get('access-control-allow-origin')}")
        
        # Check content type
        if 'application/json' in headers.get('content-type', ''):
            print("✅ Proper JSON content-type header")
        else:
            print("❌ Missing or incorrect content-type header")
            
        # Check CORS (should allow all origins as per backend config)
        if headers.get('access-control-allow-origin') == '*':
            print("✅ CORS properly configured")
            return True
        else:
            print("❌ CORS configuration issue")
            return False
            
    except Exception as e:
        print(f"❌ Headers check error: {e}")
        return False

def main():
    """Run all backend tests"""
    print("🚀 Starting Backend API Tests for Idle Game Content API")
    print("=" * 60)
    
    test_results = []
    created_pack = None
    
    # Test 1: Health endpoint
    test_results.append(("Health Endpoint", test_health_endpoint()))
    
    # Test 2: CORS and Headers
    test_results.append(("CORS and Headers", check_cors_and_headers()))
    
    # Test 3: Create content pack
    created_pack = test_create_content_pack()
    test_results.append(("Create Content Pack", created_pack is not None))
    
    if created_pack:
        pack_id = created_pack['id']
        
        # Test 4: List content packs
        packs_list = test_list_content_packs()
        test_results.append(("List Content Packs", packs_list is not None))
        
        # Test 5: Get specific content pack
        retrieved_pack = test_get_content_pack(pack_id)
        test_results.append(("Get Content Pack", retrieved_pack is not None))
        
        # Test 6: Update content pack
        updated_pack = test_update_content_pack(pack_id)
        test_results.append(("Update Content Pack", updated_pack is not None))
        
        # Test 7: Delete content pack
        delete_success = test_delete_content_pack(pack_id)
        test_results.append(("Delete Content Pack", delete_success))
        
        # Test 8: Verify deletion (should return 404)
        if delete_success:
            test_results.append(("Verify Deletion (404)", test_get_deleted_pack(pack_id)))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All backend tests passed successfully!")
        return True
    else:
        print("⚠️  Some backend tests failed. Check the details above.")
        return False

if __name__ == "__main__":
    main()