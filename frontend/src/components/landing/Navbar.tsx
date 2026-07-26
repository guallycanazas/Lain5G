import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowUpRight, Menu, X } from 'lucide-react';
import { Link } from 'react-router-dom';

const links = [
  ['Architecture', '#architecture'],
  ['Features', '#features'],
  ['Open source', '#stack'],
  ['Deploy', '#deploy'],
] as const;

export function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <motion.header className="landing-nav-shell sticky top-0 z-50" initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}>
      <div className="landing-container flex h-[74px] items-center justify-between gap-6">
        <a className="flex items-center gap-3" href="#top" aria-label="Lain5G home">
          <span className="landing-brand-avatar"><img src="/images/lain5g/lain-avatar.webp" width="512" height="512" alt="" /></span>
          <span className="grid leading-tight"><strong className="text-[1.05rem] tracking-[-.03em]">Lain5G</strong><small className="text-[.58rem] font-bold uppercase tracking-[.15em] text-violet">Open · Modular · Yours</small></span>
        </a>

        <nav className="hidden items-center gap-8 lg:flex" aria-label="Landing navigation">
          {links.map(([label, href]) => <a className="text-[.76rem] font-bold text-[#4e577c] transition-colors hover:text-violet" href={href} key={href}>{label}</a>)}
          <a className="inline-flex items-center gap-1 text-[.76rem] font-bold text-[#4e577c] hover:text-violet" href="https://github.com/guallycanazas/Lain5G" target="_blank" rel="noreferrer">GitHub <ArrowUpRight size={13} /></a>
        </nav>

        <div className="hidden lg:block"><Link className="landing-primary" to="/dashboard">Open the lab <ArrowUpRight size={15} /></Link></div>
        <button className="grid h-10 w-10 place-items-center rounded-lg border border-[#dedfec] bg-white text-navy lg:hidden" type="button" aria-label="Toggle navigation" aria-expanded={open} onClick={() => setOpen((value) => !value)}>{open ? <X size={19} /> : <Menu size={20} />}</button>
      </div>

      {open ? (
        <motion.nav className="landing-mobile-menu px-5 py-5 lg:hidden" aria-label="Mobile landing navigation" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
          <div className="mx-auto grid max-w-[1180px] gap-2">
            {links.map(([label, href]) => <a className="rounded-lg px-3 py-3 text-sm font-bold text-[#4e577c] hover:bg-[#f5f2ff]" href={href} key={href} onClick={() => setOpen(false)}>{label}</a>)}
            <a className="rounded-lg px-3 py-3 text-sm font-bold text-[#4e577c] hover:bg-[#f5f2ff]" href="https://github.com/guallycanazas/Lain5G">GitHub</a>
            <Link className="landing-primary mt-2" to="/dashboard">Open the lab</Link>
          </div>
        </motion.nav>
      ) : null}
    </motion.header>
  );
}
