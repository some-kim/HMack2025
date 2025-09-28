export interface PatientProfile {
  user_id: string;
  agent_email?: string;  // GSI field for querying patients by agent
  personal_info: {
    date_of_birth: string;
    gender: string;
    phone: string;
    address: string;
    emergency_contact: {
      name: string;
      phone: string;
      relationship: string;
    };
  };
  medical_info: {
    allergies: string[];
    medications: string[];
    conditions: string[];
    insurance: {
      provider: string;
      policy_number?: string;
    };
  };
  preferences: {
    communication_method: 'email' | 'sms' | 'both';
    appointment_reminders: boolean;
    health_tips: boolean;
  };
  created_at: string;
  updated_at: string;
}