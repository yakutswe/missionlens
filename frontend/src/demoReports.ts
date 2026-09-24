export const demoReports = [
  {
    external_id: 'DEMO-IST-001', title: 'Port activity summary',
    content: 'Synthetic observation: an unexpected change in port traffic was noted during a routine review. No real event or source is represented.',
    language: 'en', source_type: 'field_report', source_name: 'Synthetic Field Team',
    location: { latitude: 41.0082, longitude: 28.9784 }, observed_at: '2026-09-22T08:10:00Z',
  },
  {
    external_id: 'DEMO-MAD-002', title: 'Informe de infraestructura',
    content: 'Informe sintético: se observó una interrupción simulada durante una revisión de infraestructura. No describe un evento real.',
    language: 'es', source_type: 'open_source', source_name: 'Synthetic Open Feed',
    location: { latitude: 40.4168, longitude: -3.7038 }, observed_at: '2026-09-22T09:45:00Z',
  },
  {
    external_id: 'DEMO-NYC-003', title: 'Infrastructure status update',
    content: 'Synthetic observation: a fictional infrastructure status change is included to demonstrate location search and analyst case review.',
    language: 'en', source_type: 'sensor', source_name: 'Synthetic Sensor Feed',
    location: { latitude: 40.7128, longitude: -74.006 }, observed_at: '2026-09-22T10:30:00Z',
  },
  {
    external_id: 'DEMO-ANK-004', title: 'Bölgesel durum notu',
    content: 'Sentetik rapor: bölgesel durum incelemesi için tamamen kurgusal bir gözlem kaydedildi. Gerçek bir olayı anlatmaz.',
    language: 'tr', source_type: 'partner', source_name: 'Synthetic Partner Team',
    location: { latitude: 39.9334, longitude: 32.8597 }, observed_at: '2026-09-22T11:20:00Z',
  },
  {
    external_id: 'DEMO-TOK-005', title: 'Transit observation',
    content: 'Synthetic observation: a fictional transit pattern was recorded to test multilingual search, source review, and evidence selection.',
    language: 'en', source_type: 'open_source', source_name: 'Synthetic Open Feed',
    location: { latitude: 35.6762, longitude: 139.6503 }, observed_at: '2026-09-22T12:05:00Z',
  },
] as const;
