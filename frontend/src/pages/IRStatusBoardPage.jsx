import React from 'react';
import IRStatusBoard from '@/components/IRStatusBoard';

export default function IRStatusBoardPage() {
  return (
    <div className="min-h-screen bg-slate-100 p-6" data-testid="ir-status-board-page">
      <IRStatusBoard fullScreen={false} refreshInterval={15000} />
    </div>
  );
}
