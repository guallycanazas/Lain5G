import { motion } from 'framer-motion';

const projects = [
  { image: '/images/lain5g/logos/srsran.svg', imageClass: 'srsran', name: 'srsRAN', role: 'RAN 4G / 5G', detail: 'Software and SDR radio paths', href: 'https://www.srsran.com/' },
  { image: '/images/lain5g/logos/open5gs.png', imageClass: 'open5gs', name: 'Open5GS', role: 'EPC + 5GC', detail: 'Core control and user plane', href: 'https://open5gs.org/' },
  { image: '/images/lain5g/logos/kamailio.png', imageClass: 'kamailio', name: 'Kamailio', role: 'IMS core', detail: 'SIP routing and IMS signaling', href: 'https://www.kamailio.org/' },
  { image: '/images/lain5g/logos/ueransim.webp', imageClass: 'visual', name: 'UERANSIM', role: 'Software UE / gNB', detail: 'Reproducible 5G SA scenarios', href: 'https://github.com/aligungr/UERANSIM' },
  { image: '/images/lain5g/logos/fastapi.png', imageClass: 'fastapi', name: 'FastAPI', role: 'Management backend', detail: 'Local API and guarded control', href: 'https://fastapi.tiangolo.com/' },
  { image: '/images/lain5g/logos/uhd.webp', imageClass: 'visual', name: 'UHD', role: 'SDR access', detail: 'Compatible X300/X310 device support', href: 'https://github.com/EttusResearch/uhd' },
];

export function OpenSourceStack() {
  return (
    <section className="landing-section border-y border-[#e7e4f1] bg-white/55" id="stack">
      <div className="landing-container">
        <div className="mb-9 flex flex-col justify-between gap-4 md:flex-row md:items-end"><div><span className="landing-eyebrow">Open-source stack</span><h2 className="landing-display mb-0 mt-3 text-[clamp(2.1rem,3.7vw,3.15rem)] font-medium">Established projects, one coherent lab.</h2></div><p className="landing-copy mb-0 max-w-[420px] text-sm">Lain5G integrates these projects; it does not replace or reimplement them.</p></div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project, index) => (
            <motion.a className="landing-card stack-project-card" href={project.href} target="_blank" rel="noreferrer" aria-label={`Open the ${project.name} project website`} key={project.name} initial={{ opacity: 0, scale: .98 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: index * .04 }}>
              <span className={`stack-logo-stage ${project.imageClass}`}><img src={project.image} alt="" loading="lazy" decoding="async" /></span>
              <span className="stack-project-copy"><strong>{project.name}</strong><small>{project.role}</small><span>{project.detail}</span><em>Project site</em></span>
            </motion.a>
          ))}
        </div>
      </div>
    </section>
  );
}
