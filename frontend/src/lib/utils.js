import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

export const formatDateTime = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  });
};

export const formatTime = (timeString) => {
  if (!timeString) return '';
  const [hours, minutes] = timeString.split(':');
  const hour = parseInt(hours);
  const ampm = hour >= 12 ? 'PM' : 'AM';
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
};

export const calculateAge = (dateOfBirth) => {
  if (!dateOfBirth) return '';
  const today = new Date();
  const birthDate = new Date(dateOfBirth);
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }
  return age;
};

export const getRoleDisplayName = (role) => {
  const roleMap = {
    physician: 'Physician',
    nurse: 'Nurse',
    scheduler: 'Scheduler',
    admin: 'Administrator'
  };
  return roleMap[role] || role;
};

export const getStatusColor = (status) => {
  const colorMap = {
    active: 'status-active',
    pending: 'status-pending',
    completed: 'status-completed',
    cancelled: 'status-cancelled',
    scheduled: 'status-pending',
    checked_in: 'status-active',
    in_progress: 'status-active',
    no_show: 'status-critical',
    resolved: 'status-completed',
    chronic: 'status-pending',
    discontinued: 'status-cancelled'
  };
  return colorMap[status] || 'status-pending';
};
