import React from 'react';
import i18next from 'i18next';
import { I18nextProvider, initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  en: { translation: { upload: 'Upload', overlap: 'Overlap', targets: 'Targets', settings: 'Settings', results: 'Results', language: 'Language' } },
  de: { translation: { upload: 'Upload', overlap: 'Überlappung', targets: 'Ziele', settings: 'Einstellungen', results: 'Ergebnisse', language: 'Sprache' } }
};

export const I18nProvider: React.FC<React.PropsWithChildren<{ defaultLang?: 'en' | 'de' }>> = ({ children, defaultLang = 'en' }) => {
  const instanceRef = React.useRef(i18next.createInstance());

  const [ready, setReady] = React.useState(false);
  React.useEffect(() => {
    instanceRef.current
      .use(initReactI18next)
      .use(LanguageDetector)
      .init({
        resources,
        fallbackLng: defaultLang,
        detection: { order: ['querystring', 'localStorage', 'navigator'], caches: ['localStorage'] }
      })
      .then(() => setReady(true));
  }, [defaultLang]);

  if (!ready) return null;
  return <I18nextProvider i18n={instanceRef.current}>{children}</I18nextProvider>;
};

