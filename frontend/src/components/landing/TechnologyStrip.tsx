import { Boxes, Container, GitFork, RadioTower } from 'lucide-react';

const items = [
  { icon: RadioTower, label: '4G + 5G workflows', detail: 'RAN to core to data' },
  { icon: Boxes, label: 'Modular by design', detail: 'Choose only what you need' },
  { icon: Container, label: 'Local-first deploys', detail: 'Docker Compose or Kubernetes' },
  { icon: GitFork, label: 'Open and traceable', detail: 'Versioned profiles and evidence' },
];

export function TechnologyStrip() {
  return (
    <section className="technology-strip">
      <div className="landing-container grid gap-0 sm:grid-cols-2 lg:grid-cols-4">
        {items.map(({ icon: Icon, label, detail }) => (
          <div className="flex items-center gap-3 px-3 py-6 lg:justify-center" key={label}>
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#f0ecff] text-violet"><Icon size={16} /></span>
            <span className="grid gap-1"><strong className="text-[.72rem] text-navy">{label}</strong><small className="text-[.61rem] text-[#858ba7]">{detail}</small></span>
          </div>
        ))}
      </div>
    </section>
  );
}
