import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import Header from './Header';
import OnboardingFlow from './OnboardingFlow';
import DashboardContent from './DashboardContent';
import type { PatientProfile } from '../types/patient';
import { fetchPatientProfile } from '../services/api';
import Loading from './Loading';
import './Dashboard.css';

const Dashboard: React.FC = () => {
  const { user, getAccessTokenSilently } = useAuth0();
  const [patientProfile, setPatientProfile] = useState<PatientProfile | null>(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPatientData = async () => {
      try {
        const token = await getAccessTokenSilently();
        const profile = await fetchPatientProfile(token);
        setPatientProfile(profile);
      } catch (error: any) {
        if (error.response?.status === 404) {
          setIsNewUser(true);
        } else {
          console.error('Error loading patient data:', error);
        }
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      loadPatientData();
    }
  }, [user, getAccessTokenSilently]);

  const handleOnboardingComplete = (profile: PatientProfile) => {
    setPatientProfile(profile);
    setIsNewUser(false);
  };

  if (loading) {
    return <Loading />;
  }

  return (
    <div className="dashboard">
      <Header user={user} />
      {isNewUser ? (
        <OnboardingFlow onComplete={handleOnboardingComplete} />
      ) : (
        <DashboardContent patientProfile={patientProfile} />
      )}
    </div>
  );
};

export default Dashboard;