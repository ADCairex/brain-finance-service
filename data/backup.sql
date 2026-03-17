--
-- PostgreSQL database dump
--

\restrict tE91ghkvumacnFafbBTwBvda1KFoCIAzfeFSpUycG6a75qwSHWPDIyFrsgNiYww

-- Dumped from database version 17.9
-- Dumped by pg_dump version 17.9

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.accounts VALUES (1, 'Trade Republic', 1626.56);
INSERT INTO public.accounts VALUES (2, 'Imagin', 208.28);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: assets; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: investments; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.investments VALUES (1, 'CSSPX.MI', 'SP 500', 0.96454200, 621.02, '2026-03-10', 1, true, NULL);
INSERT INTO public.investments VALUES (2, 'CSSPX.MI', 'SP 500', 0.88670100, 562.76, '2025-03-10', 1, true, NULL);
INSERT INTO public.investments VALUES (3, 'CSSPX.MI', 'SP 500', 1.24296600, 561.56, '2025-03-28', 1, true, NULL);
INSERT INTO public.investments VALUES (4, 'CSSPX.MI', 'SP 500', 1.16130500, 516.66, '2025-04-28', 1, true, NULL);
INSERT INTO public.investments VALUES (5, 'CSSPX.MI', 'SP 500', 1.07428500, 557.56, '2025-05-28', 1, true, NULL);
INSERT INTO public.investments VALUES (6, 'CSSPX.MI', 'SP 500', 1.77322500, 563.38, '2025-06-30', 1, true, NULL);
INSERT INTO public.investments VALUES (7, 'CSSPX.MI', 'SP 500', 1.02141700, 586.44, '2025-07-28', 1, true, NULL);
INSERT INTO public.investments VALUES (8, 'CSSPX.MI', 'SP 500', 0.00195900, 587.03, '2025-08-11', 1, true, NULL);
INSERT INTO public.investments VALUES (9, 'CSSPX.MI', 'SP 500', 1.01237100, 591.68, '2025-08-26', 1, true, NULL);
INSERT INTO public.investments VALUES (10, 'CSSPX.MI', 'SP 500', 0.00142000, 591.55, '2025-09-09', 1, true, NULL);
INSERT INTO public.investments VALUES (11, 'CSSPX.MI', 'SP 500', 0.00668900, 598.00, '2025-09-16', 1, true, NULL);
INSERT INTO public.investments VALUES (12, 'CSSPX.MI', 'SP 500', 0.00403500, 607.19, '2025-09-23', 1, true, NULL);
INSERT INTO public.investments VALUES (13, 'CSSPX.MI', 'SP 500', 0.98965700, 605.26, '2025-09-26', 1, true, NULL);
INSERT INTO public.investments VALUES (14, 'CSSPX.MI', 'SP 500', 0.00008100, 617.28, '2025-10-02', 1, true, NULL);
INSERT INTO public.investments VALUES (15, 'CSSPX.MI', 'SP 500', 0.00053000, 622.64, '2025-10-09', 1, true, NULL);
INSERT INTO public.investments VALUES (16, 'CANG', 'Cango', 400.00000000, 1.62, '2026-03-13', 1, true, NULL);
INSERT INTO public.investments VALUES (17, 'CSSPX.MI', 'SP 500', 0.00285200, 613.60, '2025-10-16', 1, true, NULL);
INSERT INTO public.investments VALUES (18, 'CSSPX.MI', 'SP 500', 0.01026000, 619.88, '2025-10-23', 1, true, NULL);
INSERT INTO public.investments VALUES (19, 'CSSPX.MI', 'SP 500', 0.94709500, 632.46, '2025-10-28', 1, true, NULL);
INSERT INTO public.investments VALUES (20, 'CSSPX.MI', 'SP 500', 0.01238700, 635.34, '2025-11-03', 1, true, NULL);
INSERT INTO public.investments VALUES (21, 'CSSPX.MI', 'SP 500', 0.00575000, 629.57, '2025-11-10', 1, true, NULL);
INSERT INTO public.investments VALUES (22, 'CSSPX.MI', 'SP 500', 0.00816300, 623.55, '2025-11-17', 1, true, NULL);
INSERT INTO public.investments VALUES (23, 'CSSPX.MI', 'SP 500', 0.00511100, 616.32, '2025-11-24', 1, true, NULL);
INSERT INTO public.investments VALUES (24, 'CSSPX.MI', 'SP 500', 0.95170000, 629.40, '2025-11-26', 1, true, NULL);
INSERT INTO public.investments VALUES (25, 'CSSPX.MI', 'SP 500', 0.00600800, 630.83, '2025-12-02', 1, true, NULL);
INSERT INTO public.investments VALUES (26, 'CSSPX.MI', 'SP 500', 0.00285300, 630.91, '2025-12-09', 1, true, NULL);
INSERT INTO public.investments VALUES (27, 'CSSPX.MI', 'SP 500', 0.00797500, 618.18, '2025-12-16', 1, true, NULL);
INSERT INTO public.investments VALUES (28, 'CSSPX.MI', 'SP 500', 0.95846100, 624.96, '2025-12-23', 1, true, NULL);
INSERT INTO public.investments VALUES (29, 'CSSPX.MI', 'SP 500', 0.00330900, 625.57, '2025-12-23', 1, true, NULL);
INSERT INTO public.investments VALUES (30, 'CSSPX.MI', 'SP 500', 0.00455900, 629.52, '2026-01-02', 1, true, NULL);
INSERT INTO public.investments VALUES (31, 'CSSPX.MI', 'SP 500', 0.00373900, 639.21, '2026-01-09', 1, true, NULL);
INSERT INTO public.investments VALUES (32, 'CSSPX.MI', 'SP 500', 0.01145900, 641.42, '2026-01-16', 1, true, NULL);
INSERT INTO public.investments VALUES (33, 'CSSPX.MI', 'SP 500', 0.00633700, 629.64, '2026-01-23', 1, true, NULL);
INSERT INTO public.investments VALUES (34, 'CSSPX.MI', 'SP 500', 0.95385200, 627.98, '2026-01-26', 1, true, NULL);
INSERT INTO public.investments VALUES (35, 'CSSPX.MI', 'SP 500', 0.00393000, 631.04, '2026-02-02', 1, true, NULL);
INSERT INTO public.investments VALUES (38, 'NFC.DU', 'Netlix', 0.38545500, 80.42, '2026-03-13', 1, true, NULL);


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Name: accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accounts_id_seq', 2, true);


--
-- Name: assets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.assets_id_seq', 1, false);


--
-- Name: investments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.investments_id_seq', 38, true);


--
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transactions_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

\unrestrict tE91ghkvumacnFafbBTwBvda1KFoCIAzfeFSpUycG6a75qwSHWPDIyFrsgNiYww

