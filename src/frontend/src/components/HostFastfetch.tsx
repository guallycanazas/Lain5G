import { Cpu, Database, HardDrive, MemoryStick, Monitor, Server, ShieldCheck, Terminal } from 'lucide-react';
import type { PreparationReport } from '../types/preparation';

type DockerHost = NonNullable<PreparationReport['docker_host']>;

function valueOrDash(value?: string | number | null) {
  return value === null || value === undefined || value === '' ? 'Not reported' : String(value);
}

function formatSize(value?: number | null) {
  return value === null || value === undefined ? 'Not reported' : `${(value / (1024 ** 3)).toFixed(1)} GiB`;
}

function Fact({ label, value, icon: Icon }: { label: string; value: string; icon: typeof Cpu }) {
  return <div className="fastfetch-fact"><Icon size={15} aria-hidden="true" /><span>{label}</span><strong title={value}>{value}</strong></div>;
}

export function HostFastfetch({ host }: { host?: DockerHost | null }) {
  const totalDisk = host?.workspace_disk_total_bytes;
  const freeDisk = host?.workspace_disk_free_bytes;
  const usedDisk = totalDisk !== null && totalDisk !== undefined && freeDisk !== null && freeDisk !== undefined ? totalDisk - freeDisk : null;
  const usedPercent = totalDisk && usedDisk !== null ? Math.min(100, Math.max(0, Math.round((usedDisk / totalDisk) * 100))) : null;
  const os = [host?.operating_system, host?.os_version, host?.os_type].filter(Boolean).join(' · ') || 'Not reported';
  const device = [host?.manufacturer, host?.product_name].filter(Boolean).join(' · ') || 'Not reported';
  const cpu = [host?.cpu_model, host?.architecture ? `(${host.architecture})` : null].filter(Boolean).join(' ') || 'Not reported';
  const dockerContainers = host?.containers_running === null || host?.containers_running === undefined
    ? 'Not reported'
    : `${host.containers_running} running · ${valueOrDash(host.containers_stopped)} stopped · ${valueOrDash(host.containers_paused)} paused`;

  return <section className="host-fastfetch" aria-labelledby="host-fastfetch-title">
    <div className="fastfetch-terminal-bar"><div><i /><i /><i /></div><span><Terminal size={14} /> host profile</span><span>{valueOrDash(host?.name)}@openlain5g</span></div>
    <div className="fastfetch-body">
      <aside className="fastfetch-brand" aria-label="OpenLain5G host summary">
        <pre aria-hidden="true">{[
          '      ╭─────╮',
          '      │ 5G  │',
          '   ╭──┴─○─○─┴──╮',
          '   │  OPEN RAN  │',
          '   ╰───┬───┬────╯',
          '       │   │',
          '    ───┴───┴───',
        ].join('\n')}</pre>
        <strong>OpenLain5G</strong><span>HOST PROFILE</span>
      </aside>
      <div className="fastfetch-details">
        <div className="fastfetch-intro"><span>System information</span><h2 id="host-fastfetch-title">{valueOrDash(host?.name)}</h2><p>{os}</p></div>
        <div className="fastfetch-facts">
          <Fact icon={Monitor} label="Machine" value={device} />
          <Fact icon={ShieldCheck} label="Platform" value={valueOrDash(host?.virtualization)} />
          <Fact icon={Cpu} label="Processor" value={cpu} />
          <Fact icon={Monitor} label="Cores / threads" value={[host?.physical_cores === null || host?.physical_cores === undefined ? null : `${host.physical_cores} cores`, host?.cpus === null || host?.cpus === undefined ? null : `${host.cpus} threads`].filter(Boolean).join(' / ') || 'Not reported'} />
          <Fact icon={MemoryStick} label="Memory" value={formatSize(host?.memory_bytes)} />
          <Fact icon={ShieldCheck} label="Kernel" value={valueOrDash(host?.kernel_version)} />
          <Fact icon={HardDrive} label="Mainboard" value={valueOrDash(host?.board_name)} />
          <Fact icon={HardDrive} label="Firmware" value={[host?.firmware_vendor, host?.firmware_version].filter(Boolean).join(' · ') || 'Not reported'} />
          <Fact icon={HardDrive} label="Project filesystem" value={usedDisk === null ? 'Not reported' : `${formatSize(usedDisk)} used · ${formatSize(freeDisk)} free / ${formatSize(totalDisk)}`} />
        </div>
        {usedPercent !== null ? <div className="fastfetch-disk-meter"><div><span>Project filesystem usage</span><strong>{usedPercent}%</strong></div><div className="fastfetch-meter-track" role="progressbar" aria-label="Project filesystem used" aria-valuenow={usedPercent} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${usedPercent}%` }} /></div></div> : null}
        <div className="fastfetch-docker">
          <div className="fastfetch-docker-title"><Database size={15} /><strong>Docker environment</strong></div>
          <div className="fastfetch-docker-facts">
            <span><b>Engine</b>{valueOrDash(host?.docker_version)}</span>
            <span><b>Storage</b>{valueOrDash(host?.storage_driver)}</span>
            <span><b>Containers</b>{dockerContainers}</span>
            <span><b>Images</b>{valueOrDash(host?.images_count)} local</span>
            <span><b>Docker root</b>{valueOrDash(host?.docker_root_dir)}</span>
          </div>
        </div>
      </div>
    </div>
    <footer className="fastfetch-footer"><Server size={13} /> Platform type is detected from firmware data and CPU flags. Docker figures come from the engine; disk figures describe the project filesystem.</footer>
  </section>;
}
