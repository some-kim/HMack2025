import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import Header from './Header';
import OnboardingFlow from './OnboardingFlow';
import DashboardContent from './DashboardContent';
import type { PatientProfile } from '../types/patient';
import { fetchPatientProfile, initializePatient } from '../services/api';
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
        console.log('[Dashboard] Starting patient data load for user:', user?.sub);

        const token = await getAccessTokenSilently();
        console.log('[Dashboard] Got access token, length:', token?.length);

        const profile = await fetchPatientProfile(token);
        console.log('[Dashboard] Profile loaded successfully:', profile);
        setPatientProfile(profile);
        setIsNewUser(false);
      } catch (error: any) {
        console.log('[Dashboard] Error loading patient data:', error);
        console.log('[Dashboard] Error response status:', error.response?.status);
        console.log('[Dashboard] Error response data:', error.response?.data);
        console.log('[Dashboard] Full error object:', error);

        if (error.response?.status === 404) {
          console.log('[Dashboard] New user detected - BYPASSING onboarding for testing');
          setIsNewUser(false); // TESTING: Bypass onboarding
        } else {
          console.error('[Dashboard] Unexpected error loading patient data:', error);
          // For development, treat any error as new user to avoid getting stuck
          console.log('[Dashboard] BYPASSING onboarding for testing');
          setIsNewUser(false); // TESTING: Bypass onboarding
        }
      } finally {
        setLoading(false);
        console.log('[Dashboard] Finished loading, isNewUser:', isNewUser);
      }
    };

    if (user) {
      console.log('[Dashboard] User detected, loading patient data:', user);
      loadPatientData();
    } else {
      console.log('[Dashboard] No user detected');
      setLoading(false);
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