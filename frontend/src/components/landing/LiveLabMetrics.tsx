import { motion } from 'framer-motion';
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts';
import { CheckCircle2, Code2, Gauge } from 'lucide-react';

const spectrum = Array.from({ length: 36 }, (_, index) => ({
  frequency: (2.59 + index * .0012).toFixed(3),
  level: Math.round(18 + Math.sin(index * 1.7) * 7 + Math.sin(index * .43) * 10 + (index % 7 === 0 ? 18 : 0)),
}));

const metrics = [
  { icon: CheckCircle2, label: 'Backend tests', value: '262', detail: 'Passing locally' },
  { icon: Gauge, label: 'Line coverage', value: '77%', detail: 'Backend coverage' },
  { icon: Code2, label: 'Frontend tests', value: '42', detail: 'Passing locally' },
];

export function LiveLabMetrics() {
  return (
    <section className="landing-container py-10" aria-labelledby="metrics-title">
      <motion.div className="metric-shell grid md:grid-cols-[1.45fr_repeat(3,.72fr)]" initial={{ opacity: 0, y: 22 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: .3 }}>
        <div className="metric-card px-6 py-5">
          <div className="mb-1 flex items-center justify-between gap-3"><div><span className="landing-eyebrow" id="metrics-title">Lab signal preview</span><p className="mb-0 mt-1 text-[.65rem] text-[#868ca8]">Illustrative spectrum · no RF hardware</p></div><span className="rounded-full bg-[#f0ecff] px-2 py-1 text-[.55rem] font-bold text-violet">DEMO</span></div>
          <div className="metric-chart h-[92px] w-full" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={spectrum} margin={{ top: 8, right: 2, left: 2, bottom: 0 }}>
                <defs><linearGradient id="spectrumFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7657ff" stopOpacity=".58" /><stop offset="100%" stopColor="#7657ff" stopOpacity=".03" /></linearGradient></defs>
                <XAxis dataKey="frequency" axisLine={false} tickLine={false} ticks={[spectrum[0].frequency, spectrum[spectrum.length - 1].frequency]} />
                <Tooltip contentStyle={{ border: '1px solid #dedaf5', borderRadius: 8, fontSize: 10 }} formatter={(value) => [`${value} relative`, 'Level']} labelFormatter={(value) => `${value} GHz`} />
                <Area type="monotone" dataKey="level" stroke="#7657ff" strokeWidth={1.8} fill="url(#spectrumFill)" animationDuration={1000} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {metrics.map(({ icon: Icon, label, value, detail }, index) => (
          <motion.div className="metric-card flex flex-col justify-center px-6 py-5" key={label} initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ delay: index * .08 }}>
            <Icon className="mb-4 text-violet" size={18} />
            <span className="text-[.61rem] font-extrabold uppercase tracking-[.12em] text-[#7b829e]">{label}</span>
            <strong className="landing-display mt-2 text-[2rem] font-medium leading-none text-navy">{value}</strong>
            <small className="mt-2 text-[.63rem] text-[#858ca8]">{detail}</small>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
