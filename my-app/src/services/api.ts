import axios from 'axios';
import type { PatientProfile } from '../types/patient';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const fetchPatientProfile = async (tokenInput: string | any): Promise<PatientProfile> => {
  // Handle both string tokens and token objects
  const token = typeof tokenInput === 'string' ? tokenInput : tokenInput.access_token;
  console.log('[API] Fetching patient profile with token length:', token?.length);
  console.log('[API] API Base URL:', API_BASE_URL);

  try {
    const response = await api.get('/api/patient/profile', {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log('[API] Profile fetch successful:', response.status, response.data);
    return response.data;
  } catch (error: any) {
    console.log('[API] Profile fetch failed:', error.response?.status, error.response?.data);
    console.log('[API] Full error:', error);
    throw error;
  }
};

export const createPatientProfile = async (tokenInput: string | any, profileData: any): Promise<PatientProfile> => {
  // Handle both string tokens and token objects
  const token = typeof tokenInput === 'string' ? tokenInput : tokenInput.access_token;
  console.log('[API] Creating patient profile with data:', profileData);
  console.log('[API] Token length:', token?.length);
  console.log('[API] Token exists:', !!token);

  const headers = { Authorization: `Bearer ${token}` };
  console.log('[API] Request headers:', headers);
  console.log('[API] Full request URL:', `${API_BASE_URL}/api/patient/profile`);

  try {
    const response = await api.post('/api/patient/profile', profileData, { headers });
    console.log('[API] Profile creation successful:', response.status, response.data);
    return response.data.profile || response.data;
  } catch (error: any) {
    console.log('[API] Profile creation failed:', error.response?.status, error.response?.data);
    console.log('[API] Request that failed:', error.config);
    console.log('[API] Full error:', error);
    throw error;
  }
};

export const updatePatientProfile = async (tokenInput: string | any, updates: Partial<PatientProfile>): Promise<PatientProfile> => {
  // Handle both string tokens and token objects
  const token = typeof tokenInput === 'string' ? tokenInput : tokenInput.access_token;
  const response = await api.put('/api/patient/profile', updates, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

export const initializePatient = async (tokenInput: string | any): Promise<PatientProfile> => {
  // Handle both string tokens and token objects
  const token = typeof tokenInput === 'string' ? tokenInput : tokenInput.access_token;
  console.log('[API] Initializing patient with token length:', token?.length);

  try {
    const response = await api.post('/api/patient/initialize', {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
    console.log('[API] Patient initialization successful:', response.status, response.data);
    return response.data.profile || response.data;
  } catch (error: any) {
    console.log('[API] Patient initialization failed:', error.response?.status, error.response?.data);
    console.log('[API] Full error:', error);
    throw error;
  }
};

export const fetchPatientsByAgent = async (token: string, agentEmail: string): Promise<PatientProfile[]> => {
  const response = await api.get(`/api/patients/by-agent/${encodeURIComponent(agentEmail)}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};