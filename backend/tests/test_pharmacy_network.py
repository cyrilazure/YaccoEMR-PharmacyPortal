"""
Ghana Pharmacy Network API Tests
Tests for the comprehensive pharmacy network module with 133 pharmacies across all 16 Ghana regions.
Covers: stats, pharmacies listing, search, regions, ownership types, chains, and pharmacy details.
"""

import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPharmacyNetworkStats:
    """Test /api/pharmacy-network/stats endpoint"""
    
    def test_get_stats_returns_200(self):
        """Stats endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_stats_contains_total_pharmacies(self):
        """Stats should contain total_pharmacies count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/stats")
        data = response.json()
        assert "total_pharmacies" in data, "Missing total_pharmacies field"
        assert isinstance(data["total_pharmacies"], int), "total_pharmacies should be integer"
        assert data["total_pharmacies"] == 133, f"Expected 133 pharmacies, got {data['total_pharmacies']}"
    
    def test_stats_contains_nhis_count(self):
        """Stats should contain NHIS accredited count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/stats")
        data = response.json()
        assert "nhis_accredited" in data, "Missing nhis_accredited field"
        assert isinstance(data["nhis_accredited"], int), "nhis_accredited should be integer"
        assert data["nhis_accredited"] > 0, "Should have NHIS accredited pharmacies"
    
    def test_stats_contains_24hr_service_count(self):
        """Stats should contain 24-hour service count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/stats")
        data = response.json()
        assert "24hr_service" in data, "Missing 24hr_service field"
        assert isinstance(data["24hr_service"], int), "24hr_service should be integer"
        assert data["24hr_service"] > 0, "Should have 24-hour service pharmacies"
    
    def test_stats_contains_delivery_count(self):
        """Stats should contain delivery service count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/stats")
        data = response.json()
        assert "with_delivery" in data, "Missing with_delivery field"
        assert isinstance(data["with_delivery"], int), "with_delivery should be integer"
    
    def test_stats_contains_by_region(self):
        """Stats should contain breakdown by region"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/stats")
        data = response.json()
        assert "by_region" in data, "Missing by_region field"
        assert isinstance(data["by_region"], dict), "by_region should be a dictionary"
        assert len(data["by_region"]) > 0, "Should have region breakdown"
    
    def test_stats_contains_by_ownership(self):
        """Stats should contain breakdown by ownership type"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/stats")
        data = response.json()
        assert "by_ownership" in data, "Missing by_ownership field"
        assert isinstance(data["by_ownership"], dict), "by_ownership should be a dictionary"


class TestPharmacyNetworkList:
    """Test /api/pharmacy-network/pharmacies endpoint"""
    
    def test_list_pharmacies_returns_200(self):
        """List pharmacies endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_list_pharmacies_returns_pharmacies_array(self):
        """Response should contain pharmacies array"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies")
        data = response.json()
        assert "pharmacies" in data, "Missing pharmacies field"
        assert isinstance(data["pharmacies"], list), "pharmacies should be a list"
    
    def test_list_pharmacies_returns_total(self):
        """Response should contain total count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies")
        data = response.json()
        assert "total" in data, "Missing total field"
        assert isinstance(data["total"], int), "total should be integer"
    
    def test_list_pharmacies_pagination(self):
        """Pagination should work correctly"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?limit=10&offset=0")
        data = response.json()
        assert len(data["pharmacies"]) <= 10, "Should respect limit parameter"
        assert "limit" in data, "Should return limit in response"
        assert "offset" in data, "Should return offset in response"
    
    def test_pharmacy_has_required_fields(self):
        """Each pharmacy should have required fields"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?limit=5")
        data = response.json()
        assert len(data["pharmacies"]) > 0, "Should have at least one pharmacy"
        
        pharmacy = data["pharmacies"][0]
        required_fields = ["id", "name", "ownership_type", "region", "city", "address", "phone"]
        for field in required_fields:
            assert field in pharmacy, f"Missing required field: {field}"


class TestPharmacyNetworkSearch:
    """Test /api/pharmacy-network/pharmacies/search endpoint"""
    
    def test_search_kumasi_returns_results(self):
        """Search for Kumasi should return pharmacies"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/search?q=Kumasi")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "pharmacies" in data, "Missing pharmacies field"
        assert len(data["pharmacies"]) > 0, "Should find pharmacies in Kumasi"
        
        # Verify results contain Kumasi
        for pharmacy in data["pharmacies"]:
            assert "Kumasi" in pharmacy.get("city", "") or "Kumasi" in pharmacy.get("name", "") or "Kumasi" in pharmacy.get("address", ""), \
                f"Search result should contain Kumasi: {pharmacy}"
    
    def test_search_ernest_chemist_returns_results(self):
        """Search for Ernest Chemist should return chain pharmacies"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/search?q=Ernest")
        assert response.status_code == 200
        data = response.json()
        assert len(data["pharmacies"]) > 0, "Should find Ernest Chemist pharmacies"
    
    def test_search_returns_query_in_response(self):
        """Search response should include the query"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/search?q=Accra")
        data = response.json()
        assert "query" in data, "Should return query in response"
        assert data["query"] == "Accra", "Query should match input"
    
    def test_search_with_region_filter(self):
        """Search with region filter should work"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/search?q=Hospital&region=Greater Accra")
        assert response.status_code == 200
        data = response.json()
        # All results should be in Greater Accra
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("region") == "Greater Accra", f"Pharmacy should be in Greater Accra: {pharmacy}"
    
    def test_search_requires_minimum_query_length(self):
        """Search should require minimum query length"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/search?q=A")
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for short query, got {response.status_code}"


class TestPharmacyNetworkRegions:
    """Test /api/pharmacy-network/regions endpoint"""
    
    def test_get_regions_returns_200(self):
        """Regions endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/regions")
        assert response.status_code == 200
    
    def test_get_regions_returns_16_regions(self):
        """Should return all 16 Ghana regions"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/regions")
        data = response.json()
        assert "regions" in data, "Missing regions field"
        assert len(data["regions"]) == 16, f"Expected 16 regions, got {len(data['regions'])}"
    
    def test_regions_have_id_and_name(self):
        """Each region should have id and name"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/regions")
        data = response.json()
        for region in data["regions"]:
            assert "id" in region, "Region missing id"
            assert "name" in region, "Region missing name"
    
    def test_greater_accra_in_regions(self):
        """Greater Accra should be in regions list"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/regions")
        data = response.json()
        region_names = [r["name"] for r in data["regions"]]
        assert "Greater Accra" in region_names, "Greater Accra should be in regions"


class TestPharmacyNetworkByRegion:
    """Test /api/pharmacy-network/regions/{region}/pharmacies endpoint"""
    
    def test_get_greater_accra_pharmacies(self):
        """Should return pharmacies in Greater Accra"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/regions/Greater Accra/pharmacies")
        assert response.status_code == 200
        data = response.json()
        assert "pharmacies" in data, "Missing pharmacies field"
        assert len(data["pharmacies"]) > 0, "Should have pharmacies in Greater Accra"
        
        # Verify all are in Greater Accra
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("region") == "Greater Accra", f"Pharmacy should be in Greater Accra: {pharmacy}"
    
    def test_get_ashanti_pharmacies(self):
        """Should return pharmacies in Ashanti region"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/regions/Ashanti/pharmacies")
        assert response.status_code == 200
        data = response.json()
        assert len(data["pharmacies"]) > 0, "Should have pharmacies in Ashanti"
    
    def test_region_response_includes_region_name(self):
        """Response should include region name"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/regions/Greater Accra/pharmacies")
        data = response.json()
        assert "region" in data, "Should include region in response"
        assert data["region"] == "Greater Accra", "Region should match request"


class TestPharmacyNetworkOwnershipTypes:
    """Test /api/pharmacy-network/ownership-types endpoint"""
    
    def test_get_ownership_types_returns_200(self):
        """Ownership types endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/ownership-types")
        assert response.status_code == 200
    
    def test_ownership_types_returns_list(self):
        """Should return list of ownership types"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/ownership-types")
        data = response.json()
        assert "ownership_types" in data, "Missing ownership_types field"
        assert isinstance(data["ownership_types"], list), "ownership_types should be a list"
        assert len(data["ownership_types"]) > 0, "Should have ownership types"
    
    def test_ownership_types_have_required_fields(self):
        """Each ownership type should have id, name, description"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/ownership-types")
        data = response.json()
        for ot in data["ownership_types"]:
            assert "id" in ot, "Missing id field"
            assert "name" in ot, "Missing name field"
            assert "description" in ot, "Missing description field"
    
    def test_ghs_ownership_type_exists(self):
        """GHS ownership type should exist"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/ownership-types")
        data = response.json()
        ids = [ot["id"] for ot in data["ownership_types"]]
        assert "ghs" in ids, "GHS ownership type should exist"
    
    def test_chain_ownership_type_exists(self):
        """Chain ownership type should exist"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/ownership-types")
        data = response.json()
        ids = [ot["id"] for ot in data["ownership_types"]]
        assert "chain" in ids, "Chain ownership type should exist"


class TestPharmacyNetworkChains:
    """Test /api/pharmacy-network/chains endpoint"""
    
    def test_get_chains_returns_200(self):
        """Chains endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/chains")
        assert response.status_code == 200
    
    def test_chains_returns_list(self):
        """Should return list of chains"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/chains")
        data = response.json()
        assert "chains" in data, "Missing chains field"
        assert isinstance(data["chains"], list), "chains should be a list"
    
    def test_ernest_chemist_in_chains(self):
        """Ernest Chemist should be in chains"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/chains")
        data = response.json()
        chain_names = [c["name"] for c in data["chains"]]
        assert "Ernest Chemist" in chain_names, "Ernest Chemist should be in chains"
    
    def test_mpharma_in_chains(self):
        """mPharma should be in chains"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/chains")
        data = response.json()
        chain_names = [c["name"] for c in data["chains"]]
        assert "mPharma" in chain_names, "mPharma should be in chains"
    
    def test_kinapharma_in_chains(self):
        """Kinapharma should be in chains"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/chains")
        data = response.json()
        chain_names = [c["name"] for c in data["chains"]]
        assert "Kinapharma" in chain_names, "Kinapharma should be in chains"
    
    def test_chain_has_locations(self):
        """Each chain should have locations array"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/chains")
        data = response.json()
        for chain in data["chains"]:
            assert "locations" in chain, f"Chain {chain['name']} missing locations"
            assert "count" in chain, f"Chain {chain['name']} missing count"
            assert len(chain["locations"]) == chain["count"], "Locations count should match"


class TestPharmacyNetworkDetails:
    """Test /api/pharmacy-network/pharmacies/{id} endpoint"""
    
    def test_get_pharmacy_by_id(self):
        """Should get pharmacy details by ID"""
        # First get a pharmacy ID from the list
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?limit=1")
        pharmacies = list_response.json()["pharmacies"]
        assert len(pharmacies) > 0, "Need at least one pharmacy"
        
        pharmacy_id = pharmacies[0]["id"]
        
        # Get details
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/{pharmacy_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == pharmacy_id, "ID should match"
    
    def test_get_korle_bu_pharmacy(self):
        """Should get Korle Bu Teaching Hospital Pharmacy"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/GHS-GA-001")
        assert response.status_code == 200
        data = response.json()
        assert "Korle Bu" in data["name"], "Should be Korle Bu pharmacy"
        assert data["ownership_type"] == "ghs", "Should be GHS ownership"
    
    def test_get_nonexistent_pharmacy_returns_404(self):
        """Should return 404 for non-existent pharmacy"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/NONEXISTENT-ID")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_pharmacy_details_has_all_fields(self):
        """Pharmacy details should have all expected fields"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies/GHS-GA-001")
        data = response.json()
        
        expected_fields = ["id", "name", "ownership_type", "region", "city", "address", "phone", "status"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestPharmacyNetworkFilters:
    """Test filtering functionality"""
    
    def test_filter_by_nhis(self):
        """Should filter by NHIS accreditation"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?has_nhis=true&limit=10")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("has_nhis") == True, f"Pharmacy should have NHIS: {pharmacy}"
    
    def test_filter_by_24hr_service(self):
        """Should filter by 24-hour service"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?has_24hr_service=true&limit=10")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("has_24hr_service") == True, f"Pharmacy should have 24hr service: {pharmacy}"
    
    def test_filter_by_delivery(self):
        """Should filter by delivery service"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?has_delivery=true&limit=10")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("has_delivery") == True, f"Pharmacy should have delivery: {pharmacy}"
    
    def test_filter_by_ownership_type(self):
        """Should filter by ownership type"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?ownership_type=chain&limit=20")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("ownership_type") == "chain", f"Pharmacy should be chain: {pharmacy}"
    
    def test_filter_by_region(self):
        """Should filter by region"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-network/pharmacies?region=Ashanti&limit=20")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("region") == "Ashanti", f"Pharmacy should be in Ashanti: {pharmacy}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
