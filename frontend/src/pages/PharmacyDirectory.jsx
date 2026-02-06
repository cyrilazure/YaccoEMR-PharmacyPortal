import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue
} from '@/components/ui/select';
import {
  Table, TableBody, TableCell,
  TableHead, TableHeader, TableRow
} from '@/components/ui/table';
import { toast } from 'sonner';
import {
  Building2, Search, MapPin, Phone, Mail, Clock, 
  Shield, Truck, Star, ChevronRight, RefreshCw,
  Hospital, Store, Factory, Building, Users,
  Filter, X, Loader2, CheckCircle, Globe
} from 'lucide-react';
import { pharmacyNetworkAPI } from '@/lib/api';

const ownershipIcons = {
  ghs: Hospital,
  private_hospital: Building,
  retail: Store,
  wholesale: Factory,
  chain: Building2,
  mission: Building,
  quasi_government: Shield
};

const ownershipColors = {
  ghs: 'bg-green-100 text-green-800 border-green-200',
  private_hospital: 'bg-blue-100 text-blue-800 border-blue-200',
  retail: 'bg-purple-100 text-purple-800 border-purple-200',
  wholesale: 'bg-orange-100 text-orange-800 border-orange-200',
  chain: 'bg-cyan-100 text-cyan-800 border-cyan-200',
  mission: 'bg-amber-100 text-amber-800 border-amber-200',
  quasi_government: 'bg-indigo-100 text-indigo-800 border-indigo-200'
};

const tierColors = {
  tier_1: 'bg-emerald-500',
  tier_2: 'bg-yellow-500',
  tier_3: 'bg-gray-400'
};

export default function PharmacyDirectory() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [pharmacies, setPharmacies] = useState([]);
  const [stats, setStats] = useState(null);
  const [regions, setRegions] = useState([]);
  const [ownershipTypes, setOwnershipTypes] = useState([]);
  const [chains, setChains] = useState([]);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [selectedOwnership, setSelectedOwnership] = useState('all');
  const [showNhisOnly, setShowNhisOnly] = useState(false);
  const [show24HrOnly, setShow24HrOnly] = useState(false);
  const [showDeliveryOnly, setShowDeliveryOnly] = useState(false);
  
  // Pagination
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 50;
  
  // Dialogs
  const [selectedPharmacy, setSelectedPharmacy] = useState(null);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  
  // Active tab
  const [activeTab, setActiveTab] = useState('directory');

  const fetchPharmacies = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        limit,
        offset,
        ...(selectedRegion !== 'all' && { region: selectedRegion }),
        ...(selectedOwnership !== 'all' && { ownership_type: selectedOwnership }),
        ...(showNhisOnly && { has_nhis: true }),
        ...(show24HrOnly && { has_24hr_service: true }),
        ...(showDeliveryOnly && { has_delivery: true })
      };
      
      let response;
      if (searchQuery.length >= 2) {
        response = await pharmacyNetworkAPI.search(searchQuery, selectedRegion !== 'all' ? selectedRegion : undefined, limit);
      } else {
        response = await pharmacyNetworkAPI.listAll(params);
      }
      
      setPharmacies(response.data.pharmacies || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load pharmacies'));
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedRegion, selectedOwnership, showNhisOnly, show24HrOnly, showDeliveryOnly, offset]);

  const fetchReferenceData = useCallback(async () => {
    try {
      const [regionsRes, ownershipRes, statsRes, chainsRes] = await Promise.all([
        pharmacyNetworkAPI.getRegions(),
        pharmacyNetworkAPI.getOwnershipTypes(),
        pharmacyNetworkAPI.getStats(),
        pharmacyNetworkAPI.getChains()
      ]);
      
      setRegions(regionsRes.data.regions || []);
      setOwnershipTypes(ownershipRes.data.ownership_types || []);
      setStats(statsRes.data);
      setChains(chainsRes.data.chains || []);
    } catch (err) {
      console.error('Failed to load reference data:', err);
    }
  }, []);

  useEffect(() => {
    fetchReferenceData();
  }, [fetchReferenceData]);

  useEffect(() => {
    fetchPharmacies();
  }, [fetchPharmacies]);

  const handleSearch = (value) => {
    setSearchQuery(value);
    setOffset(0);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedRegion('all');
    setSelectedOwnership('all');
    setShowNhisOnly(false);
    setShow24HrOnly(false);
    setShowDeliveryOnly(false);
    setOffset(0);
  };

  const hasActiveFilters = searchQuery || selectedRegion !== 'all' || selectedOwnership !== 'all' || showNhisOnly || show24HrOnly || showDeliveryOnly;

  const OwnershipIcon = ({ type }) => {
    const Icon = ownershipIcons[type] || Store;
    return <Icon className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Building2 className="w-7 h-7 text-emerald-600" />
            Ghana Pharmacy Directory
          </h1>
          <p className="text-slate-500 mt-1">
            Comprehensive national database of {stats?.total_pharmacies || 0} pharmacies across all 16 regions
          </p>
        </div>
        <Button onClick={fetchPharmacies} variant="outline" className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-emerald-800">{stats.total_pharmacies}</p>
                <p className="text-sm text-emerald-600">Total Pharmacies</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-blue-800">{stats.nhis_accredited}</p>
                <p className="text-sm text-blue-600">NHIS Accredited</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-purple-800">{stats['24hr_service']}</p>
                <p className="text-sm text-purple-600">24-Hour Service</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-amber-800">{stats.with_delivery}</p>
                <p className="text-sm text-amber-600">Delivery Available</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-cyan-50 to-cyan-100 border-cyan-200">
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-cyan-800">{Object.keys(stats.by_region || {}).length}</p>
                <p className="text-sm text-cyan-600">Regions Covered</p>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-rose-50 to-rose-100 border-rose-200">
            <CardContent className="pt-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-rose-800">{chains.length}</p>
                <p className="text-sm text-rose-600">Pharmacy Chains</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-3 w-full max-w-md">
          <TabsTrigger value="directory" className="gap-2">
            <Building2 className="w-4 h-4" /> Directory
          </TabsTrigger>
          <TabsTrigger value="chains" className="gap-2">
            <Store className="w-4 h-4" /> Chains
          </TabsTrigger>
          <TabsTrigger value="regions" className="gap-2">
            <MapPin className="w-4 h-4" /> By Region
          </TabsTrigger>
        </TabsList>

        {/* Directory Tab */}
        <TabsContent value="directory" className="mt-4 space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search by name, city, or address..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10"
                data-testid="pharmacy-search-input"
              />
            </div>
            
            <Select value={selectedRegion} onValueChange={setSelectedRegion}>
              <SelectTrigger className="w-48" data-testid="region-filter">
                <SelectValue placeholder="All Regions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Regions</SelectItem>
                {regions.map(r => (
                  <SelectItem key={r.id} value={r.name}>{r.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={selectedOwnership} onValueChange={setSelectedOwnership}>
              <SelectTrigger className="w-48" data-testid="ownership-filter">
                <SelectValue placeholder="All Types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {ownershipTypes.map(ot => (
                  <SelectItem key={ot.id} value={ot.id}>{ot.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-1">
                <X className="w-4 h-4" /> Clear
              </Button>
            )}
          </div>
          
          {/* Quick Filters */}
          <div className="flex flex-wrap gap-2">
            <Button
              variant={showNhisOnly ? "default" : "outline"}
              size="sm"
              onClick={() => setShowNhisOnly(!showNhisOnly)}
              className="gap-1"
              data-testid="nhis-filter-btn"
            >
              <Shield className="w-4 h-4" /> NHIS Accredited
            </Button>
            <Button
              variant={show24HrOnly ? "default" : "outline"}
              size="sm"
              onClick={() => setShow24HrOnly(!show24HrOnly)}
              className="gap-1"
              data-testid="24hr-filter-btn"
            >
              <Clock className="w-4 h-4" /> 24-Hour Service
            </Button>
            <Button
              variant={showDeliveryOnly ? "default" : "outline"}
              size="sm"
              onClick={() => setShowDeliveryOnly(!showDeliveryOnly)}
              className="gap-1"
              data-testid="delivery-filter-btn"
            >
              <Truck className="w-4 h-4" /> Delivery Available
            </Button>
          </div>
          
          {/* Results */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  {loading ? 'Loading...' : `${total} Pharmacies Found`}
                </CardTitle>
                {total > limit && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={offset === 0}
                      onClick={() => setOffset(Math.max(0, offset - limit))}
                    >
                      Previous
                    </Button>
                    <span className="text-sm text-gray-500">
                      {offset + 1}-{Math.min(offset + limit, total)} of {total}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={offset + limit >= total}
                      onClick={() => setOffset(offset + limit)}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                </div>
              ) : pharmacies.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Building2 className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No pharmacies found matching your criteria</p>
                </div>
              ) : (
                <ScrollArea className="h-[500px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Pharmacy</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Location</TableHead>
                        <TableHead>Contact</TableHead>
                        <TableHead>Services</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pharmacies.map((pharmacy) => (
                        <TableRow 
                          key={pharmacy.id} 
                          className="hover:bg-gray-50 cursor-pointer"
                          onClick={() => {
                            setSelectedPharmacy(pharmacy);
                            setDetailsDialogOpen(true);
                          }}
                          data-testid={`pharmacy-row-${pharmacy.id}`}
                        >
                          <TableCell>
                            <div className="flex items-start gap-3">
                              <div className={`w-2 h-full rounded-full ${tierColors[pharmacy.tier] || 'bg-gray-400'}`} />
                              <div>
                                <p className="font-medium text-gray-900">{pharmacy.name}</p>
                                <p className="text-sm text-gray-500">{pharmacy.license_number || 'N/A'}</p>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge className={`${ownershipColors[pharmacy.ownership_type] || 'bg-gray-100'} gap-1`}>
                              <OwnershipIcon type={pharmacy.ownership_type} />
                              {pharmacy.ownership_type?.replace(/_/g, ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div>
                              <p className="font-medium">{pharmacy.city}</p>
                              <p className="text-sm text-gray-500">{pharmacy.region}</p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="text-sm">
                              <p className="flex items-center gap-1">
                                <Phone className="w-3 h-3" /> {pharmacy.phone}
                              </p>
                              {pharmacy.email && (
                                <p className="flex items-center gap-1 text-gray-500">
                                  <Mail className="w-3 h-3" /> {pharmacy.email}
                                </p>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-wrap gap-1">
                              {pharmacy.has_nhis && (
                                <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                                  NHIS
                                </Badge>
                              )}
                              {pharmacy.has_24hr_service && (
                                <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700 border-purple-200">
                                  24hr
                                </Badge>
                              )}
                              {pharmacy.has_delivery && (
                                <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                                  Delivery
                                </Badge>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button 
                              size="sm" 
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPharmacy(pharmacy);
                                setDetailsDialogOpen(true);
                              }}
                            >
                              View <ChevronRight className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Chains Tab */}
        <TabsContent value="chains" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {chains.map((chain) => (
              <Card key={chain.name} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-cyan-600" />
                      {chain.name}
                    </CardTitle>
                    <Badge className="bg-cyan-100 text-cyan-800">
                      {chain.count} locations
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-40">
                    <div className="space-y-2">
                      {chain.locations.map((loc) => (
                        <div 
                          key={loc.id} 
                          className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                          onClick={() => {
                            pharmacyNetworkAPI.getById(loc.id).then(res => {
                              setSelectedPharmacy(res.data);
                              setDetailsDialogOpen(true);
                            });
                          }}
                        >
                          <div>
                            <p className="font-medium text-sm">{loc.city}</p>
                            <p className="text-xs text-gray-500">{loc.region}</p>
                          </div>
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Regions Tab */}
        <TabsContent value="regions" className="mt-4">
          {stats && stats.by_region && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.by_region)
                .sort((a, b) => b[1] - a[1])
                .map(([region, count]) => (
                  <Card 
                    key={region} 
                    className="hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => {
                      setSelectedRegion(region);
                      setActiveTab('directory');
                    }}
                  >
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{region}</p>
                          <p className="text-2xl font-bold text-emerald-600">{count}</p>
                          <p className="text-sm text-gray-500">pharmacies</p>
                        </div>
                        <MapPin className="w-8 h-8 text-gray-300" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Pharmacy Details Dialog */}
      <Dialog open={detailsDialogOpen} onOpenChange={setDetailsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-600" />
              Pharmacy Details
            </DialogTitle>
            <DialogDescription>
              {selectedPharmacy?.id}
            </DialogDescription>
          </DialogHeader>
          
          {selectedPharmacy && (
            <div className="space-y-4 py-4">
              {/* Header Info */}
              <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-lg p-4">
                <h3 className="text-xl font-bold text-emerald-900">{selectedPharmacy.name}</h3>
                <div className="flex flex-wrap gap-2 mt-2">
                  <Badge className={ownershipColors[selectedPharmacy.ownership_type] || 'bg-gray-100'}>
                    {selectedPharmacy.ownership_type?.replace(/_/g, ' ')}
                  </Badge>
                  {selectedPharmacy.has_nhis && (
                    <Badge className="bg-green-500 text-white">NHIS Accredited</Badge>
                  )}
                  {selectedPharmacy.has_24hr_service && (
                    <Badge className="bg-purple-500 text-white">24-Hour Service</Badge>
                  )}
                  {selectedPharmacy.has_delivery && (
                    <Badge className="bg-blue-500 text-white">Delivery Available</Badge>
                  )}
                </div>
              </div>

              {/* Location & Contact */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                    <MapPin className="w-4 h-4" /> Location
                  </h4>
                  <div className="space-y-2 text-sm">
                    <p><span className="text-gray-500">Address:</span> {selectedPharmacy.address}</p>
                    <p><span className="text-gray-500">City:</span> {selectedPharmacy.city}</p>
                    <p><span className="text-gray-500">Region:</span> {selectedPharmacy.region}</p>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-700 mb-3 flex items-center gap-2">
                    <Phone className="w-4 h-4" /> Contact
                  </h4>
                  <div className="space-y-2 text-sm">
                    <p className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-gray-400" />
                      {selectedPharmacy.phone}
                    </p>
                    {selectedPharmacy.email && (
                      <p className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-gray-400" />
                        {selectedPharmacy.email}
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Operating Hours */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-700 mb-2 flex items-center gap-2">
                  <Clock className="w-4 h-4" /> Operating Hours
                </h4>
                <p className="text-blue-900">{selectedPharmacy.operating_hours || 'Not specified'}</p>
              </div>

              {/* Parent Facility (if applicable) */}
              {selectedPharmacy.parent_facility && (
                <div className="bg-amber-50 rounded-lg p-4">
                  <h4 className="font-medium text-amber-700 mb-2 flex items-center gap-2">
                    <Hospital className="w-4 h-4" /> Parent Facility
                  </h4>
                  <p className="text-amber-900">{selectedPharmacy.parent_facility}</p>
                </div>
              )}

              {/* License Info */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">License Number:</span>
                  <span className="font-mono">{selectedPharmacy.license_number || 'N/A'}</span>
                </div>
                <div className="flex items-center justify-between text-sm mt-1">
                  <span className="text-gray-500">Tier:</span>
                  <Badge className={tierColors[selectedPharmacy.tier] + ' text-white'}>
                    {selectedPharmacy.tier?.replace(/_/g, ' ').toUpperCase()}
                  </Badge>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setDetailsDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
