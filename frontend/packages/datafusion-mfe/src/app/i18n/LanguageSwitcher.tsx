import React from 'react';
import { MenuItem, Select } from '@mui/material';
import { useTranslation } from 'react-i18next';

export const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const [lang, setLang] = React.useState(i18n.language?.startsWith('de') ? 'de' : 'en');
  React.useEffect(() => {
    i18n.changeLanguage(lang);
  }, [lang, i18n]);
  return (
    <Select size="small" value={lang} onChange={(e) => setLang(e.target.value)} sx={{ color: 'white', borderColor: 'white', ml: 2 }}>
      <MenuItem value="en">EN</MenuItem>
      <MenuItem value="de">DE</MenuItem>
    </Select>
  );
};

