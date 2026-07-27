import { motion } from 'framer-motion';
import { ArrowRight, Github, Radio } from 'lucide-react';
import { Link } from 'react-router';
import { NetworkArchitectureIllustration } from './NetworkArchitectureIllustration';

export function HeroSection() {
  return (
    <section className="landing-hero" id="top">
      <div className="landing-container landing-hero-grid">
        <motion.div className="landing-hero-copy" initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: .7 }}>
          <div className="landing-hero-tags mb-7 flex flex-wrap gap-2">
            {['Open source', '4G / 5G', 'Private networks'].map((tag) => <span className="rounded-full border border-[#ded9fa] bg-white/70 px-3 py-1.5 text-[.61rem] font-extrabold uppercase tracking-[.12em] text-violet" key={tag}>{tag}</span>)}
          </div>
          <h1 className="landing-display landing-hero-title">Your network.<br />Your lab.<br /><span>Your rules.</span></h1>
          <p className="landing-copy mx-auto mb-8 max-w-[520px] lg:mx-0">Build and study isolated mobile networks with a reproducible stack for RAN, core, IMS, subscribers, orchestration, and validation. Start in software, then move to guarded SDR paths when your lab is ready.</p>
          <div className="landing-hero-actions flex flex-wrap gap-3">
            <Link className="landing-primary" to="/dashboard"><Radio size={16} /> Open the lab <ArrowRight size={15} /></Link>
            <a className="landing-secondary" href="https://github.com/guallycanazas/Lain5G" target="_blank" rel="noreferrer"><Github size={17} /> View on GitHub</a>
          </div>
          <p className="mt-6 text-[.67rem] font-semibold leading-relaxed text-[#8188a5]">Research and education software · RF disabled by default · MIT licensed</p>
        </motion.div>

        <motion.div className="landing-architecture-wrap" id="architecture" initial={{ opacity: 0, scale: .97 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: .9, delay: .12 }}>
          <NetworkArchitectureIllustration />
        </motion.div>
      </div>
    </section>
  );
}
