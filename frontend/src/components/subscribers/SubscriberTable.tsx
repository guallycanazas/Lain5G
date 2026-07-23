import { Link } from 'react-router-dom';
import { Copy, Eye, KeyRound, Pencil, Trash2 } from 'lucide-react';
import type { SubscriberSummary } from '../../types/subscriber';

interface SubscriberTableProps {
  subscribers: SubscriberSummary[];
  onClone: (subscriber: SubscriberSummary) => void;
  onDelete: (subscriber: SubscriberSummary) => void;
}

export function SubscriberTable({ subscribers, onClone, onDelete }: SubscriberTableProps) {
  return (
    <div className="table-wrap subscriber-table-wrap">
      <table className="subscriber-table">
        <thead>
          <tr>
            <th>IMSI</th>
            <th>MSISDN</th>
            <th>Network profile</th>
            <th>Authentication</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {subscribers.map((subscriber) => (
            <tr key={subscriber.imsi}>
              <td><span className="subscriber-id">{subscriber.imsi}</span></td>
              <td>{subscriber.msisdn || 'n/a'}</td>
              <td><strong>{subscriber.dnn || 'n/a'}</strong><span className="table-secondary">S-NSSAI {subscriber.sst ?? 'n/a'} / {subscriber.sd || 'n/a'}</span></td>
              <td><div className="security-flags"><span className={subscriber.security.k_configured ? 'configured' : ''}><KeyRound size={12} />K</span><span className={subscriber.security.op_configured ? 'configured' : ''}>OP</span><span className={subscriber.security.opc_configured ? 'configured' : ''}>OPc</span></div></td>
              <td><div className="row-actions">
                <Link className="row-action" to={`/subscribers/${subscriber.imsi}`} title="View"><Eye size={15} /><span>View</span></Link>
                <Link className="row-action" to={`/subscribers/${subscriber.imsi}/edit`} title="Edit"><Pencil size={15} /><span>Edit</span></Link>
                <button className="row-action secondary" onClick={() => onClone(subscriber)}><Copy size={15} /><span>Clone</span></button>
                <button className="row-action danger" onClick={() => onDelete(subscriber)}><Trash2 size={15} /><span>Delete</span></button>
              </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
