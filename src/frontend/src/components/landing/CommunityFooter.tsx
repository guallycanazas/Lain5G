import { ArrowUpRight, Github, RadioTower } from 'lucide-react';
import { Link } from 'react-router';

export function CommunityFooter() {
  return (
    <footer className="community-footer" id="community">
      <img className="footer-network-art" src="/images/lain5g/footer-network-girl.webp" width="2014" height="781" alt="Illustrated network researcher standing among telecommunications infrastructure" loading="lazy" decoding="async" />
      <div className="landing-container relative z-10 flex min-h-[430px] items-center py-14">
        <div className="community-footer-copy ml-auto w-full max-w-[620px]">
          <span className="text-[.64rem] font-extrabold uppercase tracking-[.16em] text-[#6748f4]">A networked systems laboratory</span>
          <h2 className="landing-display my-5 text-[clamp(2.6rem,5vw,4.7rem)] font-medium leading-[1.02]">The network is yours.<br />The lab is yours.<br /><span className="text-[#a68cff]">Let&apos;s build carefully.</span></h2>
          <p className="mb-8 max-w-[590px] text-sm leading-7 text-[#5f6685]">Created at the National University of San Agustin of Arequipa for reproducible mobile-network research and education.</p>
          <div className="mb-10 grid gap-4 sm:grid-cols-3">
            {[['License', 'MIT'], ['Release', import.meta.env.VITE_APP_VERSION], ['Default', 'RF disabled']].map(([label, value]) => <div className="border-l border-[#c8c2ed] pl-4" key={label}><span className="block text-[.58rem] font-bold uppercase tracking-[.13em] text-[#777c9d]">{label}</span><strong className="mt-2 block text-[.9rem] text-[#18214f]">{value}</strong></div>)}
          </div>
          <div className="flex flex-wrap items-center gap-4">
            <Link className="landing-primary" to="/dashboard"><RadioTower size={16} /> Open the lab</Link>
            <a className="footer-link inline-flex items-center gap-2 text-sm font-bold" href="https://github.com/guallycanazas/Lain5G" target="_blank" rel="noreferrer"><Github size={17} /> GitHub <ArrowUpRight size={14} /></a>
            <a className="footer-link text-sm font-bold" href="https://github.com/guallycanazas/Lain5G/tree/main/docs">Documentation</a>
          </div>
        </div>
      </div>
      <div className="relative z-10 border-t border-[#dcd9ed]"><div className="landing-container flex flex-col justify-between gap-2 py-5 text-[.61rem] text-[#777c9d] sm:flex-row"><span>OpenLain5G · Open research software</span><span>Built for transparent, bounded claims</span></div></div>
    </footer>
  );
}
