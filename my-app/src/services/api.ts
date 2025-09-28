import axios from 'axios';
import type { PatientProfile } from '../types/patient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const fetchPatientProfile = async (token: string): Promise<PatientProfile> => {
  const response = await api.get('/api/patient/profile', {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const createPatientProfile = async (token: string, profileData: any): Promise<PatientProfile> => {
  const response = await api.post('/api/patient/profile', profileData, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const updatePatientProfile = async (token: string, updates: Partial<PatientProfile>): Promise<PatientProfile> => {
  const response = await api.put('/api/patient/profile', updates, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const fetchPatientsByAgent = async (token: string, agentEmail: string): Promise<PatientProfile[]> => {
  const response = await api.get(`/api/patients/by-agent/${encodeURIComponent(agentEmail)}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};