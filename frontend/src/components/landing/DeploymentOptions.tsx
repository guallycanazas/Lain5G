import { motion } from 'framer-motion';

const options = [
  { image: '/images/lain5g/lab-recipes.webp', imageClass: 'recipe', title: 'Local lab', badge: 'Available', text: 'Run isolated software scenarios with Docker Compose on one GNU/Linux workstation.', command: 'make start-5g-sa' },
  { image: '/images/lain5g/hero-topology.webp', imageClass: 'topology', title: 'Operator interface', badge: 'Available', text: 'Use the FastAPI and React management plane in observation-only mode by default.', command: 'make app-up' },
  { image: '/images/lain5g/deployment-cluster.webp', imageClass: 'cluster', title: 'Kubernetes', badge: 'Design target', text: 'Extend the same component boundaries toward cluster orchestration with explicit site integration.', command: 'Kubernetes · Helm / Kustomize' },
];

export function DeploymentOptions() {
  return (
    <section className="deploy-section landing-section" id="deploy">
      <div className="landing-container relative z-10">
        <div className="deployment-overview">
          <div className="deployment-intro"><span className="landing-eyebrow">Deployment options</span><h2 className="landing-display mb-4 mt-3 text-[clamp(2.5rem,4vw,3.7rem)] font-medium leading-[1.04]">Run it<br />your way.</h2><p className="landing-copy mb-0 max-w-[460px] text-sm">Start from a local Compose lab. Keep orchestration boundaries clear as the environment grows.</p></div>
          <figure className="deployment-visual"><img src="/images/lain5g/deployment-cluster.webp" width="1536" height="1024" alt="Illustrated container cluster representing deployment and orchestration boundaries" loading="lazy" decoding="async" /><figcaption><span>Current path</span><strong>Compose is available today. Kubernetes remains a design target.</strong></figcaption></figure>
        </div>
        <div className="deployment-card-grid">
          {options.map(({ image, imageClass, title, badge, text, command }, index) => (
            <motion.article className="landing-card deployment-card" key={title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: index * .08 }}>
              <div className="deployment-card-media"><img className={imageClass} src={image} alt="" loading="lazy" decoding="async" /><span className="deployment-badge">{badge}</span></div>
              <div className="deployment-card-body"><span className="deployment-index">0{index + 1}</span><h3>{title}</h3><p>{text}</p><code className="deployment-command">{command}</code></div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
