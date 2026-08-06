import { CommunityFooter } from '../components/landing/CommunityFooter';
import { DeploymentOptions } from '../components/landing/DeploymentOptions';
import { FeaturesGrid } from '../components/landing/FeaturesGrid';
import { HeroSection } from '../components/landing/HeroSection';
import { LiveLabMetrics } from '../components/landing/LiveLabMetrics';
import { Navbar } from '../components/landing/Navbar';
import { OpenSourceStack } from '../components/landing/OpenSourceStack';
import { TechnologyStrip } from '../components/landing/TechnologyStrip';
import '../landing.css';

export function LandingPage() {
  return (
    <div className="landing-page min-h-screen overflow-hidden bg-ivory text-navy">
      <Navbar />
      <main>
        <HeroSection />
        <TechnologyStrip />
        <LiveLabMetrics />
        <FeaturesGrid />
        <OpenSourceStack />
        <DeploymentOptions />
      </main>
      <CommunityFooter />
    </div>
  );
}
