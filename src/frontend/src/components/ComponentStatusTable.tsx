import { StatusBadge } from './StatusBadge';
import type { ComponentImageStatus } from '../types/preparation';
import { usePreferences } from '../preferences/PreferencesProvider';


export function ComponentStatusTable({ images }: { images: ComponentImageStatus[] }) {
  const { t } = usePreferences();
  return <div className="table-wrap"><table><thead><tr><th>{t('preparation.component')}</th><th>{t('preparation.publishedSource')}</th><th>{t('preparation.state')}</th></tr></thead><tbody>{images.map((image) => <tr key={image.local_image}><td><strong>{image.description}</strong><code className="component-ref">{image.local_image}</code></td><td><code>{image.source_image}</code></td><td><StatusBadge status={image.installed ? 'PASS' : 'FAIL'} kind="validation" /></td></tr>)}</tbody></table></div>;
}
