import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import {
  Pill, MapPin, Phone, Mail, Clock, Shield, ArrowLeft,
  Building2, CheckCircle, Globe, Truck, Star, Loader2
} from 'lucide-react';
import api from '@/lib/api';

// Pharmacy API
const pharmacyAPI = {
  getPharmacy: (id) => api.get(`/pharmacy-portal/public/pharmacies/${id}`),
};

export default function PharmacyProfile() {
  const { pharmacyId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [pharmacy, setPharmacy] = useState(null);
  const [services, setServices] = useState([]);

  useEffect(() => {
    const fetchPharmacy = async () => {
      try {
        const response = await pharmacyAPI.getPharmacy(pharmacyId);
        setPharmacy(response.data.pharmacy);
        setServices(response.data.services || []);
      } catch (error) {
        toast.error('Failed to load pharmacy details');
        navigate('/pharmacy');
      } finally {
        setLoading(false);
      }
    };

    fetchPharmacy();
  }, [pharmacyId, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!pharmacy) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-slate-500">Pharmacy not found</p>
          <Button onClick={() => navigate('/pharmacy')} className="mt-4">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Directory
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="pharmacy-profile">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <Button variant="ghost" onClick={() => navigate('/pharmacy')} className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Directory
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Pharmacy Header Card */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-start gap-6">
              <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-blue-600 rounded-2xl flex items-center justify-center">
                <Pill className="w-10 h-10 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <h1 className="text-2xl font-bold text-slate-900">{pharmacy.name}</h1>
                    <div className="flex items-center gap-2 mt-1">
                      <MapPin className="w-4 h-4 text-slate-400" />
                      <span className="text-slate-600">{pharmacy.city || pharmacy.town}, {pharmacy.region}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <Badge className={`${
                      pharmacy.ownership_type === 'ghs' ? 'bg-green-100 text-green-700' :
                      pharmacy.ownership_type === 'retail' ? 'bg-blue-100 text-blue-700' :
                      pharmacy.ownership_type === 'chain' ? 'bg-purple-100 text-purple-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {pharmacy.ownership_type?.replace(/_/g, ' ').toUpperCase() || 'PHARMACY'}
                    </Badge>
                    {pharmacy.rating > 0 && (
                      <div className="flex items-center gap-1 mt-2 justify-end">
                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                        <span className="font-semibold">{pharmacy.rating?.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                  {pharmacy.has_nhis && (
                    <Badge className="bg-green-100 text-green-700">
                      <Shield className="w-3 h-3 mr-1" /> NHIS Accredited
                    </Badge>
                  )}
                  {pharmacy.has_24hr_service && (
                    <Badge className="bg-blue-100 text-blue-700">
                      <Clock className="w-3 h-3 mr-1" /> 24/7 Service
                    </Badge>
                  )}
                  {pharmacy.has_delivery && (
                    <Badge className="bg-purple-100 text-purple-700">
                      <Truck className="w-3 h-3 mr-1" /> Delivery Available
                    </Badge>
                  )}
                  {pharmacy.tier === 'tier_1' && (
                    <Badge className="bg-yellow-100 text-yellow-700">
                      <Star className="w-3 h-3 mr-1" /> Premium Tier
                    </Badge>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Contact Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Phone className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Phone</p>
                  <p className="font-medium">{pharmacy.phone || 'Not available'}</p>
                </div>
              </div>

              {pharmacy.email && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Mail className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Email</p>
                    <p className="font-medium">{pharmacy.email}</p>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Clock className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Operating Hours</p>
                  <p className="font-medium">{pharmacy.operating_hours || 'Not specified'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Location */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Location</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Address</p>
                  <p className="font-medium">{pharmacy.address}</p>
                  {pharmacy.gps_address && (
                    <p className="text-sm text-slate-400">GPS: {pharmacy.gps_address}</p>
                  )}
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                  <Globe className="w-5 h-5 text-slate-600" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">Region / District</p>
                  <p className="font-medium">{pharmacy.region}</p>
                  {pharmacy.district && (
                    <p className="text-sm text-slate-400">{pharmacy.district}</p>
                  )}
                </div>
              </div>

              {/* Map Placeholder */}
              <div className="h-48 bg-slate-100 rounded-lg flex items-center justify-center">
                <div className="text-center text-slate-400">
                  <MapPin className="w-8 h-8 mx-auto mb-2" />
                  <p className="text-sm">Map view coming soon</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* License Information */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">License & Accreditation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-slate-500">License Number</p>
                  <p className="font-mono font-medium">{pharmacy.license_number || 'Not provided'}</p>
                </div>
              </div>

              {pharmacy.parent_facility && (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Building2 className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-slate-500">Parent Facility</p>
                    <p className="font-medium">{pharmacy.parent_facility}</p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Services (Future) */}
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-lg">Services</CardTitle>
            <CardDescription>Available pharmacy services</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-4 bg-slate-50 rounded-lg text-center">
                <Pill className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <p className="text-sm font-medium">Prescription Dispensing</p>
              </div>
              {pharmacy.has_nhis && (
                <div className="p-4 bg-slate-50 rounded-lg text-center">
                  <Shield className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                  <p className="text-sm font-medium">NHIS Processing</p>
                </div>
              )}
              {pharmacy.has_delivery && (
                <div className="p-4 bg-slate-50 rounded-lg text-center">
                  <Truck className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                  <p className="text-sm font-medium">Home Delivery</p>
                </div>
              )}
              <div className="p-4 bg-slate-50 rounded-lg text-center border-2 border-dashed border-slate-200">
                <p className="text-sm text-slate-400">More services coming soon</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Placeholder sections */}
        <div className="mt-6 grid md:grid-cols-2 gap-6">
          <Card className="border-dashed">
            <CardHeader>
              <CardTitle className="text-lg text-slate-400">Drug Inventory</CardTitle>
              <CardDescription>Coming soon</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">
                View available medications and stock levels at this pharmacy.
              </p>
            </CardContent>
          </Card>

          <Card className="border-dashed">
            <CardHeader>
              <CardTitle className="text-lg text-slate-400">Insurance Partners</CardTitle>
              <CardDescription>Coming soon</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">
                View accepted insurance providers and coverage information.
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
