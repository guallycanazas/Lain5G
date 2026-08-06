import { motion } from 'framer-motion';

const features = [
  { image: '/images/lain5g/hero-topology.webp', imageClass: 'topology', title: 'End-to-end building blocks', text: 'Compose RAN, EPC or 5GC, subscribers, and validation without hiding component boundaries.' },
  { image: '/images/lain5g/lab-recipes.webp', imageClass: 'recipe-start', title: 'Docker first', text: 'Keep software scenarios isolated, repeatable, and straightforward to inspect on one workstation.' },
  { image: '/images/lain5g/deployment-cluster.webp', imageClass: 'cluster', title: 'Orchestration path', text: 'Carry clear component boundaries from the local lab toward a future cluster-managed deployment.' },
  { image: '/images/lain5g/lab-recipes.webp', imageClass: 'recipe-middle', title: 'Declarative profiles', text: 'Version network intent while keeping site-specific and sensitive values outside Git.' },
  { image: '/images/lain5g/sdr-hardware.webp', imageClass: 'hardware', title: 'Guarded operations', text: 'Observation is the default; mutations, Docker control, and RF each require explicit opt-in.' },
  { image: '/images/lain5g/lab-recipes.webp', imageClass: 'recipe-end', title: 'Evidence aware', text: 'Separate passing software checks from hardware, commercial-UE, voice, and RF claims.' },
];

export function FeaturesGrid() {
  return (
    <section className="landing-section" id="features">
      <div className="landing-container">
        <div className="mb-10 max-w-[720px]"><span className="landing-eyebrow">Private network workbench</span><h2 className="landing-display mb-4 mt-3 text-[clamp(2.25rem,4vw,3.4rem)] font-medium leading-tight">Everything you need to understand the stack.</h2><p className="landing-copy mb-0">A practical interface for assembling open mobile-network components without overstating what the lab has validated.</p></div>
        <div className="feature-card-grid">
          {features.map(({ image, imageClass, title, text }, index) => (
            <motion.article className="landing-card feature-card" key={title} initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .2 }} transition={{ delay: index * .05 }}>
              <div className="feature-card-media"><img className={imageClass} src={image} alt="" loading="lazy" decoding="async" /><span>0{index + 1}</span></div>
              <div className="feature-card-body"><h3>{title}</h3><p>{text}</p></div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
