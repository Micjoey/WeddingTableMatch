import React, { useState } from 'react';
import { useAppStore } from '../../store';
import { Guest } from '../../types';

// ---- Private field sub-components ----

const TextField: React.FC<{
  label: string;
  value: string;
  onChange: (v: string) => void;
}> = ({ label, value, onChange }) => (
  <div>
    <label className="block text-xs text-gray-600 mb-1">{label}</label>
    <input
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
  </div>
);

const NumberField: React.FC<{
  label: string;
  value: number;
  min?: number;
  onChange: (v: number) => void;
}> = ({ label, value, min = 0, onChange }) => (
  <div>
    <label className="block text-xs text-gray-600 mb-1">{label}</label>
    <input
      type="number"
      min={min}
      value={value}
      onChange={e => onChange(Number(e.target.value))}
      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
  </div>
);

const CheckField: React.FC<{
  label: string;
  hint?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}> = ({ label, hint, checked, onChange }) => (
  <label className="flex items-start gap-3 cursor-pointer">
    <div className="mt-0.5 shrink-0">
      <div
        onClick={() => onChange(!checked)}
        className={`w-8 h-4 rounded-full relative transition-colors cursor-pointer ${checked ? 'bg-blue-500' : 'bg-gray-200'}`}
      >
        <div className={`absolute top-0.5 w-3 h-3 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-4' : 'translate-x-0.5'}`} />
      </div>
    </div>
    <div>
      <p className="text-xs font-medium text-gray-700">{label}</p>
      {hint && <p className="text-[11px] text-gray-400 mt-0.5">{hint}</p>}
    </div>
  </label>
);

const ArrayField: React.FC<{
  label: string;
  value: string[];
  onChange: (v: string[]) => void;
}> = ({ label, value, onChange }) => (
  <div>
    <label className="block text-xs text-gray-600 mb-1">{label}</label>
    <input
      type="text"
      value={value.join(', ')}
      onChange={e =>
        onChange(
          e.target.value
            .split(',')
            .map(s => s.trim())
            .filter(Boolean)
        )
      }
      className="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    />
    <p className="text-[10px] text-gray-400 mt-0.5">Comma-separated</p>
  </div>
);

// ---- Main Modal ----

export const GuestEditModal: React.FC<{ guest: Guest; onClose: () => void }> = ({
  guest,
  onClose,
}) => {
  const updateGuest = useAppStore(s => s.updateGuest);
  const [draft, setDraft] = useState<Guest>({ ...guest });

  function update<K extends keyof Guest>(key: K, value: Guest[K]) {
    setDraft(d => ({ ...d, [key]: value }));
  }

  function handleSave() {
    updateGuest(guest.name, draft);
    onClose();
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between shrink-0">
          <h2 className="text-lg font-semibold text-gray-900">Edit Guest</h2>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto flex-1 px-6 py-4 space-y-6">
          {/* Basic Info */}
          <section className="space-y-3">
            <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">Basic Info</h3>
            <TextField label="Name" value={draft.name} onChange={v => update('name', v)} />
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="Age" value={draft.age} onChange={v => update('age', v)} />
              <TextField label="Gender Identity" value={draft.gender_identity} onChange={v => update('gender_identity', v)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <TextField label="RSVP" value={draft.rsvp} onChange={v => update('rsvp', v)} />
              <TextField label="Location" value={draft.location} onChange={v => update('location', v)} />
            </div>
          </section>

          {/* Meal & Diet */}
          <section className="space-y-3">
            <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">Meal &amp; Diet</h3>
            <TextField label="Meal Preference" value={draft.meal_preference} onChange={v => update('meal_preference', v)} />
            <ArrayField label="Diet Choices" value={draft.diet_choices} onChange={v => update('diet_choices', v)} />
          </section>

          {/* Social */}
          <section className="space-y-3">
            <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">Social</h3>
            <TextField label="Relationship Status" value={draft.relationship_status} onChange={v => update('relationship_status', v)} />
            <TextField label="Partner" value={draft.partner} onChange={v => update('partner', v)} />
            <div className="grid grid-cols-2 gap-4">
              <CheckField label="Single" checked={draft.single} onChange={v => update('single', v)} />
              <CheckField label="Plus One" checked={draft.plus_one} onChange={v => update('plus_one', v)} />
              <CheckField label="Sit With Partner" checked={draft.sit_with_partner} onChange={v => update('sit_with_partner', v)} />
            </div>
            <ArrayField label="Interested In" value={draft.interested_in} onChange={v => update('interested_in', v)} />
          </section>

          {/* Seating Constraints */}
          <section className="space-y-3">
            <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">Seating Constraints</h3>
            <ArrayField label="Groups" value={draft.groups} onChange={v => update('groups', v)} />
            <ArrayField label="Must Sit With" value={draft.must_with} onChange={v => update('must_with', v)} />
            <ArrayField label="Must Separate From" value={draft.must_separate} onChange={v => update('must_separate', v)} />
            <TextField label="Forced Table" value={draft.forced_table} onChange={v => update('forced_table', v)} />
            <div className="grid grid-cols-3 gap-3">
              <NumberField label="Min Known" value={draft.min_known} onChange={v => update('min_known', v)} />
              <NumberField label="Min Unknown" value={draft.min_unknown} onChange={v => update('min_unknown', v)} />
              <NumberField label="Weight" value={draft.weight} min={1} onChange={v => update('weight', v)} />
            </div>
          </section>

          {/* Interests */}
          <section className="space-y-3">
            <h3 className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest">Interests</h3>
            <ArrayField label="Hobbies" value={draft.hobbies} onChange={v => update('hobbies', v)} />
            <ArrayField label="Languages" value={draft.languages} onChange={v => update('languages', v)} />
          </section>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-3 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};
