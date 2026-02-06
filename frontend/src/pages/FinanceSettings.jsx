import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
  Building2, Plus, Trash2, Edit, CheckCircle,
  Smartphone, CreditCard, Loader2, Shield
} from 'lucide-react';
import api from '@/lib/api';

const financeAPI = {
  getBankAccounts: () => api.get('/finance/bank-accounts'),
  createBankAccount: (data) => api.post('/finance/bank-accounts', data),
  updateBankAccount: (id, data) => api.put(`/finance/bank-accounts/${id}`, data),
  deleteBankAccount: (id) => api.delete(`/finance/bank-accounts/${id}`),
  getMobileMoneyAccounts: () => api.get('/finance/mobile-money-accounts'),
  createMobileMoneyAccount: (data) => api.post('/finance/mobile-money-accounts', data),
};

export default function FinanceSettings() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [mobileMoneyAccounts, setMobileMoneyAccounts] = useState([]);
  const [addBankDialogOpen, setAddBankDialogOpen] = useState(false);
  const [editBankDialogOpen, setEditBankDialogOpen] = useState(false);
  const [addMoMoDialogOpen, setAddMoMoDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  
  const [bankForm, setBankForm] = useState({
    bank_name: '',
    account_name: '',
    account_number: '',
    branch: '',
    swift_code: '',
    account_type: 'current',
    currency: 'GHS',
    is_primary: false
  });
  
  const [momoForm, setMomoForm] = useState({
    provider: 'MTN',
    account_name: '',
    mobile_number: '',
    wallet_id: '',
    is_primary: false
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [bankRes, momoRes] = await Promise.all([
        financeAPI.getBankAccounts(),
        financeAPI.getMobileMoneyAccounts()
      ]);
      
      setBankAccounts(bankRes.data.accounts || []);
      setMobileMoneyAccounts(momoRes.data.accounts || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load finance settings'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddBankAccount = async (e) => {
    e.preventDefault();
    if (!bankForm.bank_name || !bankForm.account_number) {
      toast.error('Bank name and account number are required');
      return;
    }
    
    setSaving(true);
    try {
      await financeAPI.createBankAccount(bankForm);
      toast.success('Bank account added successfully');
      setAddBankDialogOpen(false);
      setBankForm({
        bank_name: '', account_name: '', account_number: '',
        branch: '', swift_code: '', account_type: 'current',
        currency: 'GHS', is_primary: false
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add bank account'));
    } finally {
      setSaving(false);
    }
  };

  const handleAddMoMoAccount = async (e) => {
    e.preventDefault();
    if (!momoForm.account_name || !momoForm.mobile_number) {
      toast.error('Account name and mobile number are required');
      return;
    }
    
    setSaving(true);
    try {
      await financeAPI.createMobileMoneyAccount(momoForm);
      toast.success('Mobile money account added');
      setAddMoMoDialogOpen(false);
      setMomoForm({
        provider: 'MTN', account_name: '', mobile_number: '',
        wallet_id: '', is_primary: false
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add mobile money account'));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteBankAccount = async (accountId) => {
    if (!confirm('Are you sure you want to remove this bank account?')) return;
    
    try {
      await financeAPI.deleteBankAccount(accountId);
      toast.success('Bank account removed');
      fetchData();
    } catch (err) {
      toast.error('Failed to remove account');
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Building2 className="w-7 h-7 text-emerald-600" />
          Finance Settings
        </h1>
        <p className="text-slate-500 mt-1">Manage hospital banking and payment accounts</p>
      </div>

      <Tabs defaultValue="bank" className="w-full">
        <TabsList>
          <TabsTrigger value="bank" className="gap-2">
            <Building2 className="w-4 h-4" /> Bank Accounts
          </TabsTrigger>
          <TabsTrigger value="momo" className="gap-2">
            <Smartphone className="w-4 h-4" /> Mobile Money
          </TabsTrigger>
        </TabsList>

        {/* Bank Accounts Tab */}
        <TabsContent value="bank" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Bank Accounts</CardTitle>
                <CardDescription>Hospital bank accounts for receiving payments</CardDescription>
              </div>
              <Button onClick={() => setAddBankDialogOpen(true)} className="gap-2">
                <Plus className="w-4 h-4" /> Add Bank Account
              </Button>
            </CardHeader>
            <CardContent>
              {bankAccounts.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Building2 className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No bank accounts configured</p>
                  <Button onClick={() => setAddBankDialogOpen(true)} className="mt-4" variant="outline">
                    <Plus className="w-4 h-4 mr-2" /> Add Your First Account
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Bank Name</TableHead>
                      <TableHead>Account Name</TableHead>
                      <TableHead>Account Number</TableHead>
                      <TableHead>Branch</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bankAccounts.map((account) => (
                      <TableRow key={account.id}>
                        <TableCell className="font-medium">{account.bank_name}</TableCell>
                        <TableCell>{account.account_name}</TableCell>
                        <TableCell className="font-mono">{account.account_number}</TableCell>
                        <TableCell className="text-sm text-gray-500">{account.branch || 'N/A'}</TableCell>
                        <TableCell className="capitalize">{account.account_type}</TableCell>
                        <TableCell>
                          {account.is_primary ? (
                            <Badge className="bg-emerald-100 text-emerald-700">
                              <CheckCircle className="w-3 h-3 mr-1" /> Primary
                            </Badge>
                          ) : (
                            <Badge variant="outline">Secondary</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDeleteBankAccount(account.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Mobile Money Tab */}
        <TabsContent value="momo" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Mobile Money Accounts</CardTitle>
                <CardDescription>MTN, Vodafone, AirtelTigo wallet accounts</CardDescription>
              </div>
              <Button onClick={() => setAddMoMoDialogOpen(true)} className="gap-2">
                <Plus className="w-4 h-4" /> Add Mobile Money
              </Button>
            </CardHeader>
            <CardContent>
              {mobileMoneyAccounts.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Smartphone className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No mobile money accounts configured</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Provider</TableHead>
                      <TableHead>Account Name</TableHead>
                      <TableHead>Mobile Number</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {mobileMoneyAccounts.map((account) => (
                      <TableRow key={account.id}>
                        <TableCell className="font-medium">{account.provider}</TableCell>
                        <TableCell>{account.account_name}</TableCell>
                        <TableCell className="font-mono">{account.mobile_number}</TableCell>
                        <TableCell>
                          {account.is_primary ? (
                            <Badge className="bg-emerald-100 text-emerald-700">Primary</Badge>
                          ) : (
                            <Badge variant="outline">Secondary</Badge>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="ghost" className="text-red-600">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Bank Account Dialog */}
      <Dialog open={addBankDialogOpen} onOpenChange={setAddBankDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add Bank Account</DialogTitle>
            <DialogDescription>Configure hospital bank account for receiving payments</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleAddBankAccount} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Bank Name *</Label>
                <Input
                  value={bankForm.bank_name}
                  onChange={(e) => setBankForm({...bankForm, bank_name: e.target.value})}
                  placeholder="e.g., GCB Bank, Ecobank Ghana"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Account Name *</Label>
                <Input
                  value={bankForm.account_name}
                  onChange={(e) => setBankForm({...bankForm, account_name: e.target.value})}
                  placeholder="Hospital account name"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Account Number *</Label>
                <Input
                  value={bankForm.account_number}
                  onChange={(e) => setBankForm({...bankForm, account_number: e.target.value})}
                  placeholder="Account number"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Branch</Label>
                <Input
                  value={bankForm.branch}
                  onChange={(e) => setBankForm({...bankForm, branch: e.target.value})}
                  placeholder="e.g., Accra Main"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Account Type</Label>
                <Select value={bankForm.account_type} onValueChange={(v) => setBankForm({...bankForm, account_type: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="current">Current Account</SelectItem>
                    <SelectItem value="savings">Savings Account</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>SWIFT Code (Optional)</Label>
                <Input
                  value={bankForm.swift_code}
                  onChange={(e) => setBankForm({...bankForm, swift_code: e.target.value})}
                  placeholder="For international transfers"
                />
              </div>
            </div>
            
            <div className="flex items-center gap-2 p-3 bg-emerald-50 rounded-lg">
              <input
                type="checkbox"
                id="primary-bank"
                checked={bankForm.is_primary}
                onChange={(e) => setBankForm({...bankForm, is_primary: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="primary-bank" className="text-emerald-700 font-medium">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                Set as primary account for receiving payments
              </Label>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddBankDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Add Bank Account
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Mobile Money Dialog */}
      <Dialog open={addMoMoDialogOpen} onOpenChange={setAddMoMoDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Mobile Money Account</DialogTitle>
            <DialogDescription>Configure mobile money wallet for payments</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleAddMoMoAccount} className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Provider *</Label>
              <Select value={momoForm.provider} onValueChange={(v) => setMomoForm({...momoForm, provider: v})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MTN">MTN Mobile Money</SelectItem>
                  <SelectItem value="Vodafone">Vodafone Cash</SelectItem>
                  <SelectItem value="AirtelTigo">AirtelTigo Money</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Account Name *</Label>
              <Input
                value={momoForm.account_name}
                onChange={(e) => setMomoForm({...momoForm, account_name: e.target.value})}
                placeholder="Hospital name on mobile money"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label>Mobile Number *</Label>
              <Input
                value={momoForm.mobile_number}
                onChange={(e) => setMomoForm({...momoForm, mobile_number: e.target.value})}
                placeholder="e.g., 0244123456"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label>Wallet ID (Optional)</Label>
              <Input
                value={momoForm.wallet_id}
                onChange={(e) => setMomoForm({...momoForm, wallet_id: e.target.value})}
                placeholder="Merchant/Wallet ID if applicable"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="primary-momo"
                checked={momoForm.is_primary}
                onChange={(e) => setMomoForm({...momoForm, is_primary: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="primary-momo">Set as primary mobile money account</Label>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddMoMoDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Add Mobile Money
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
