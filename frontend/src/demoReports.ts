// Every observation below is fictional; the source labels represent demo roles.
export const scenarioReportIds = [
  'SCENARIO-IST-101',
  'SCENARIO-IST-102',
  'SCENARIO-IST-103',
] as const;

export const scenarioCase = {
  title: 'Review synthetic terminal access reports',
  summary: 'Compare three fictional reports of a terminal access delay. Check whether they describe the same event and leave the cause unverified until an analyst reviews the sources.',
};

export const demoReports = [
  {
    external_id: scenarioReportIds[0], title: 'Terminal access observation',
    content: 'Fictional field observation: vehicles waited longer than usual near a terminal entrance. The observer did not identify the cause. This report is synthetic.',
    language: 'en', source_type: 'field_report', source_name: 'Synthetic Field Team',
    location: { latitude: 41.0082, longitude: 28.9784 }, observed_at: '2026-09-22T08:10:00Z',
  },
  {
    external_id: scenarioReportIds[1], title: 'Terminal giriş notu',
    content: 'Kurgusal saha notu: terminal girişinde araçların bekleme süresi uzadı. Nedeni doğrulanmadı. Bu rapor tamamen sentetiktir.',
    language: 'tr', source_type: 'partner', source_name: 'Synthetic Partner Team',
    location: { latitude: 41.0087, longitude: 28.9811 }, observed_at: '2026-09-22T08:24:00Z',
  },
  {
    external_id: scenarioReportIds[2], title: 'Resumen de acceso a la terminal',
    content: 'Informe ficticio: se observó congestión cerca de la entrada de la terminal. No se ha verificado la causa ni si se trata del mismo evento. Datos sintéticos.',
    language: 'es', source_type: 'open_source', source_name: 'Synthetic Open Feed',
    location: { latitude: 41.0092, longitude: 28.9796 }, observed_at: '2026-09-22T08:41:00Z',
  },
  {
    external_id: 'SCENARIO-NYC-201', title: 'Unrelated infrastructure update',
    content: 'Fictional infrastructure status update in another city. This report is unrelated to the synthetic terminal access observations.',
    language: 'en', source_type: 'sensor', source_name: 'Synthetic Sensor Feed',
    location: { latitude: 40.7128, longitude: -74.006 }, observed_at: '2026-09-22T10:30:00Z',
  },
  {
    external_id: 'SCENARIO-TOK-202', title: 'Unrelated transit observation',
    content: 'Fictional transit observation in a different region. It provides an unrelated result when filtering and choosing case evidence.',
    language: 'en', source_type: 'open_source', source_name: 'Synthetic Open Feed',
    location: { latitude: 35.6762, longitude: 139.6503 }, observed_at: '2026-09-22T12:05:00Z',
  },
] as const;
